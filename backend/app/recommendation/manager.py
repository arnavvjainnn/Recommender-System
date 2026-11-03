import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from app.config import settings
from app.models.db_models import Product, Interaction, Order, OrderItem, Category, UserPreferences, ModelMetrics
from app.recommendation.content_based import ContentBasedRecommender
from app.recommendation.collaborative import CollaborativeRecommender
from app.recommendation.popularity import PopularityRecommender
from app.recommendation.association_rules import AssociationRulesRecommender
from app.recommendation.hybrid import HybridRecommender
from app.recommendation.explainability import ExplanationEngine
from app.schemas.pydantic_models import RecommendedProductResponse, ProductResponse, RecommendationExplanation

logger = logging.getLogger(__name__)

class RecommendationManager:
    """
    Central Orchestrator & Cache Manager for all recommendation models.
    Provides thread-safe access, model serialization/deserialization,
    and automatic fallback routing.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecommendationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.content_model = ContentBasedRecommender()
        self.collab_model = CollaborativeRecommender()
        self.pop_model = PopularityRecommender()
        self.rules_model = AssociationRulesRecommender()
        self.hybrid_engine: Optional[HybridRecommender] = None
        
        self.is_trained = False
        self._load_or_init()
        self._initialized = True

    def _load_or_init(self):
        try:
            if (
                settings.CONTENT_SIMILARITY_PATH.exists() and
                settings.COLLABORATIVE_MODEL_PATH.exists() and
                settings.POPULARITY_MODEL_PATH.exists() and
                settings.ASSOCIATION_RULES_PATH.exists()
            ):
                logger.info("Loading precomputed ML models from disk...")
                self.content_model.load()
                self.collab_model.load()
                self.pop_model.load()
                self.rules_model.load()
                self.is_trained = True
                self._rebuild_hybrid()
                logger.info("ML models successfully loaded from disk.")
        except Exception as e:
            logger.warning(f"Failed to load models from disk: {e}. Will fit from database.")

    def _rebuild_hybrid(self, weights_config=None):
        w_collab = weights_config.weight_collaborative if weights_config else settings.WEIGHT_COLLABORATIVE
        w_content = weights_config.weight_content if weights_config else settings.WEIGHT_CONTENT
        w_pop = weights_config.weight_popularity if weights_config else settings.WEIGHT_POPULARITY
        mmr_lambda = weights_config.mmr_diversity_lambda if weights_config else settings.MMR_DIVERSITY_LAMBDA

        self.hybrid_engine = HybridRecommender(
            content_model=self.content_model,
            collab_model=self.collab_model,
            pop_model=self.pop_model,
            weight_collab=w_collab,
            weight_content=w_content,
            weight_pop=w_pop,
            mmr_lambda=mmr_lambda
        )

    def train(self, db: Session, weights_config=None) -> Dict[str, any]:
        """
        Executes end-to-end multi-model training over the current database state,
        serializes the artifacts to disk, and updates the in-memory inference engines.
        """
        logger.info("Starting multi-model training pipeline...")
        # 1. Fetch products
        db_products = db.query(Product).all()
        products_data = []
        for p in db_products:
            cat_name = p.category.name if p.category else ""
            products_data.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "category_id": p.category_id,
                "category_name": cat_name,
                "subcategory": p.subcategory,
                "brand": p.brand,
                "price": p.price,
                "rating": p.rating,
                "rating_count": p.rating_count,
                "stock": p.stock,
                "tags": p.tags,
                "is_active": p.is_active
            })

        # 2. Fetch interactions
        db_interactions = db.query(Interaction).all()
        interactions_data = [
            {
                "user_id": i.user_id,
                "product_id": i.product_id,
                "interaction_type": i.interaction_type,
                "implicit_weight": i.implicit_weight,
                "created_at": i.created_at
            }
            for i in db_interactions
        ]

        # 3. Fetch Orders for Association Rules
        db_orders = db.query(Order).all()
        orders_baskets = []
        for o in db_orders:
            basket = [item.product_id for item in o.items]
            if len(basket) > 1:
                orders_baskets.append(basket)

        # 4. Train Models
        self.content_model.fit(products_data)
        self.collab_model.fit(interactions_data)
        self.pop_model.fit(interactions_data, products_data)
        self.rules_model.fit(orders_baskets)

        # 5. Save Artifacts to Disk
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        self.content_model.save()
        self.collab_model.save()
        self.pop_model.save()
        self.rules_model.save()

        self.is_trained = True
        self._rebuild_hybrid(weights_config)
        logger.info("Multi-model training and serialization complete.")

        return {
            "products_indexed": len(products_data),
            "interactions_trained": len(interactions_data),
            "baskets_mined": len(orders_baskets),
            "status": "ready"
        }

    def _ensure_ready(self, db: Session):
        if not self.is_trained:
            self.train(db)

    def _get_product_meta_map(self, db: Session) -> Dict[str, dict]:
        products = db.query(Product).all()
        meta_map = {}
        for p in products:
            cat_name = p.category.name if p.category else ""
            meta_map[p.id] = {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "category_id": p.category_id,
                "category_name": cat_name,
                "subcategory": p.subcategory,
                "brand": p.brand,
                "price": p.price,
                "discount_percent": p.discount_percent,
                "rating": p.rating,
                "rating_count": p.rating_count,
                "stock": p.stock,
                "image_url": p.image_url,
                "tags": json.loads(p.tags) if isinstance(p.tags, str) and p.tags.startswith("[") else [],
                "is_active": p.is_active,
                "created_at": p.created_at
            }
        return meta_map

    def get_personalized(
        self,
        db: Session,
        user_id: Optional[str],
        session_id: str,
        limit: int = 10
    ) -> List[RecommendedProductResponse]:
        self._ensure_ready(db)
        meta_map = self._get_product_meta_map(db)

        # Gather user interaction history
        user_interactions: List[Tuple[str, float]] = []
        user_recent_titles: List[str] = []
        excluded_pids: Set[str] = set()

        if user_id:
            interactions = (
                db.query(Interaction)
                .filter(Interaction.user_id == user_id)
                .order_by(Interaction.created_at.desc())
                .limit(50)
                .all()
            )
            for inter in interactions:
                user_interactions.append((inter.product_id, inter.implicit_weight))
                if inter.product_id in meta_map and len(user_recent_titles) < 3:
                    user_recent_titles.append(meta_map[inter.product_id]["title"])
                # Exclude already purchased items
                if inter.interaction_type == "PURCHASE":
                    excluded_pids.add(inter.product_id)

        # Fallback to session interactions if guest or empty user profile
        if not user_interactions and session_id:
            session_interactions = (
                db.query(Interaction)
                .filter(Interaction.session_id == session_id)
                .order_by(Interaction.created_at.desc())
                .limit(20)
                .all()
            )
            for inter in session_interactions:
                user_interactions.append((inter.product_id, inter.implicit_weight))
                if inter.product_id in meta_map and len(user_recent_titles) < 3:
                    user_recent_titles.append(meta_map[inter.product_id]["title"])

        # Fetch onboarding preferences if available
        preferences: List[str] = []
        if user_id:
            user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()
            preferences = [p.category_name for p in user_prefs]

        # Execute Hybrid Recommender
        recommendations = self.hybrid_engine.recommend(
            user_id=user_id,
            user_interactions=user_interactions,
            user_preferences=preferences,
            all_product_metadata=meta_map,
            excluded_product_ids=excluded_pids,
            top_k=limit
        )

        response = []
        for rec in recommendations:
            pid = rec["product_id"]
            if pid not in meta_map:
                continue
            p_data = meta_map[pid]
            explanation = ExplanationEngine.generate_explanation(
                breakdown=rec["breakdown"],
                product_metadata=p_data,
                user_recent_item_titles=user_recent_titles
            )
            product_resp = ProductResponse(
                id=p_data["id"],
                title=p_data["title"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                category_name=p_data["category_name"],
                subcategory=p_data["subcategory"],
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data["discount_percent"],
                rating=p_data["rating"],
                rating_count=p_data["rating_count"],
                stock=p_data["stock"],
                image_url=p_data["image_url"],
                tags=p_data["tags"],
                is_active=p_data["is_active"],
                created_at=p_data["created_at"]
            )
            response.append(RecommendedProductResponse(
                product=product_resp,
                score=rec["score"],
                explanation=explanation
            ))

        return response

    def get_similar_products(self, db: Session, product_id: str, limit: int = 6) -> List[RecommendedProductResponse]:
        self._ensure_ready(db)
        meta_map = self._get_product_meta_map(db)
        if product_id not in meta_map:
            return []

        source_product = meta_map[product_id]
        similar_items = self.content_model.get_similar_items(product_id, top_n=limit)

        response = []
        for pid, sim_score in similar_items:
            if pid not in meta_map:
                continue
            p_data = meta_map[pid]
            explanation = RecommendationExplanation(
                primary_factor="CONTENT_SIMILARITY",
                reason_text=f"Matches the style, category, and features of '{source_product['title']}'.",
                content_score=round(sim_score, 4),
                final_score=round(sim_score, 4)
            )
            product_resp = ProductResponse(
                id=p_data["id"],
                title=p_data["title"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                category_name=p_data["category_name"],
                subcategory=p_data["subcategory"],
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data["discount_percent"],
                rating=p_data["rating"],
                rating_count=p_data["rating_count"],
                stock=p_data["stock"],
                image_url=p_data["image_url"],
                tags=p_data["tags"],
                is_active=p_data["is_active"],
                created_at=p_data["created_at"]
            )
            response.append(RecommendedProductResponse(
                product=product_resp,
                score=sim_score,
                explanation=explanation
            ))

        return response

    def get_frequently_bought_together(self, db: Session, product_id: str, limit: int = 4) -> List[RecommendedProductResponse]:
        self._ensure_ready(db)
        meta_map = self._get_product_meta_map(db)
        if product_id not in meta_map:
            return []

        source_product = meta_map[product_id]
        rules = self.rules_model.get_frequently_bought_together(product_id, top_n=limit)

        # Fallback to high content similarity if basket count is low
        if not rules:
            return self.get_similar_products(db, product_id, limit=limit)

        response = []
        for r in rules:
            consequent_id = r["consequent_id"]
            if consequent_id not in meta_map:
                continue
            p_data = meta_map[consequent_id]
            explanation = RecommendationExplanation(
                primary_factor="FREQUENT_BUNDLE",
                reason_text=f"Frequently purchased together with '{source_product['title']}' (Lift: {r['lift']}).",
                final_score=r["confidence"]
            )
            product_resp = ProductResponse(
                id=p_data["id"],
                title=p_data["title"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                category_name=p_data["category_name"],
                subcategory=p_data["subcategory"],
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data["discount_percent"],
                rating=p_data["rating"],
                rating_count=p_data["rating_count"],
                stock=p_data["stock"],
                image_url=p_data["image_url"],
                tags=p_data["tags"],
                is_active=p_data["is_active"],
                created_at=p_data["created_at"]
            )
            response.append(RecommendedProductResponse(
                product=product_resp,
                score=r["confidence"],
                explanation=explanation
            ))

        return response

    def get_trending(self, db: Session, limit: int = 10) -> List[RecommendedProductResponse]:
        self._ensure_ready(db)
        meta_map = self._get_product_meta_map(db)
        trending_items = self.pop_model.get_top_trending(top_n=limit)

        response = []
        for pid, score in trending_items:
            if pid not in meta_map:
                continue
            p_data = meta_map[pid]
            explanation = RecommendationExplanation(
                primary_factor="POPULAR_TRENDING",
                reason_text=f"Trending this week in {p_data['category_name']} with high purchase velocity.",
                popularity_score=round(score, 4),
                final_score=round(score, 4)
            )
            product_resp = ProductResponse(
                id=p_data["id"],
                title=p_data["title"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                category_name=p_data["category_name"],
                subcategory=p_data["subcategory"],
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data["discount_percent"],
                rating=p_data["rating"],
                rating_count=p_data["rating_count"],
                stock=p_data["stock"],
                image_url=p_data["image_url"],
                tags=p_data["tags"],
                is_active=p_data["is_active"],
                created_at=p_data["created_at"]
            )
            response.append(RecommendedProductResponse(
                product=product_resp,
                score=score,
                explanation=explanation
            ))

        return response

    def get_popular(self, db: Session, limit: int = 10) -> List[RecommendedProductResponse]:
        self._ensure_ready(db)
        meta_map = self._get_product_meta_map(db)
        popular_items = self.pop_model.get_top_popular(top_n=limit)

        response = []
        for pid, score in popular_items:
            if pid not in meta_map:
                continue
            p_data = meta_map[pid]
            explanation = RecommendationExplanation(
                primary_factor="POPULAR_TRENDING",
                reason_text=f"All-time customer favorite in {p_data['category_name']} with {p_data['rating']}★ rating.",
                popularity_score=round(score, 4),
                final_score=round(score, 4)
            )
            product_resp = ProductResponse(
                id=p_data["id"],
                title=p_data["title"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                category_name=p_data["category_name"],
                subcategory=p_data["subcategory"],
                brand=p_data["brand"],
                price=p_data["price"],
                discount_percent=p_data["discount_percent"],
                rating=p_data["rating"],
                rating_count=p_data["rating_count"],
                stock=p_data["stock"],
                image_url=p_data["image_url"],
                tags=p_data["tags"],
                is_active=p_data["is_active"],
                created_at=p_data["created_at"]
            )
            response.append(RecommendedProductResponse(
                product=product_resp,
                score=score,
                explanation=explanation
            ))

        return response

# Global Singleton Manager
recommendation_manager = RecommendationManager()
