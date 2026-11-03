import math
import random
import time
import numpy as np
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.db_models import Product, Interaction, ModelMetrics
from app.recommendation.content_based import ContentBasedRecommender
from app.recommendation.collaborative import CollaborativeRecommender
from app.recommendation.popularity import PopularityRecommender
from app.recommendation.hybrid import HybridRecommender

class RecSysEvaluator:
    """
    Offline Recommendation Evaluation Framework.
    Implements Leave-Last-K Temporal Splitting with Negative Sampling (1:99 ratio)
    and computes standard Information Retrieval (IR) metrics:
    Precision@K, Recall@K, HitRate@K, NDCG@K, MAP@K, Catalog Coverage, and Diversity.
    """
    def __init__(self, k_values: List[int] = [5, 10]):
        self.k_values = k_values
        self.max_k = max(k_values)

    def temporal_split(self, interactions: List[dict], test_ratio: float = 0.20) -> Tuple[List[dict], Dict[str, Set[str]]]:
        """
        Partitions user interactions chronologically.
        Returns (train_interactions, test_ground_truth_by_user).
        """
        user_interactions = defaultdict(list)
        for inter in interactions:
            uid = inter.get("user_id")
            if uid:
                user_interactions[uid].append(inter)

        train_interactions = []
        test_ground_truth = defaultdict(set)

        for uid, events in user_interactions.items():
            # Sort chronologically
            events.sort(key=lambda x: x.get("created_at") or datetime.min)
            n_events = len(events)
            if n_events < 5:
                train_interactions.extend(events)
                continue

            split_idx = int(n_events * (1.0 - test_ratio))
            train_events = events[:split_idx]
            test_events = events[split_idx:]

            train_interactions.extend(train_events)
            for t in test_events:
                test_ground_truth[uid].add(t["product_id"])

        return train_interactions, test_ground_truth

    def evaluate_model(
        self,
        model_name: str,
        predict_fn,
        test_ground_truth: Dict[str, Set[str]],
        all_product_ids: List[str],
        sim_matrix: Optional[np.ndarray],
        prod_idx_map: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Runs evaluation over all test users with 99 negative item sampling.
        """
        start_time = time.time()
        precisions_5, recalls_5 = [], []
        precisions_10, recalls_10 = [], []
        hit_rates_10 = []
        ndcgs_10 = []
        maps_10 = []
        recommended_all_items: Set[str] = set()
        diversity_scores = []

        all_pids_set = set(all_product_ids)

        for user_id, actual_positives in test_ground_truth.items():
            if not actual_positives:
                continue

            # Identify unobserved negative items for user
            unobserved = list(all_pids_set - actual_positives)
            if len(unobserved) < 99:
                sample_negatives = unobserved
            else:
                sample_negatives = random.sample(unobserved, 99)

            # Test pool = actual positives + sampled negatives
            candidate_pool = list(actual_positives) + sample_negatives

            # Rank items using model prediction function
            ranked_items = predict_fn(user_id, candidate_pool, top_k=self.max_k)
            top_10 = ranked_items[:10]
            top_5 = ranked_items[:5]

            recommended_all_items.update(top_10)

            # 1. Precision & Recall @ 5
            hits_5 = len(set(top_5) & actual_positives)
            precisions_5.append(hits_5 / 5.0)
            recalls_5.append(hits_5 / len(actual_positives))

            # 2. Precision, Recall & HitRate @ 10
            hits_10 = len(set(top_10) & actual_positives)
            precisions_10.append(hits_10 / 10.0)
            recalls_10.append(hits_10 / len(actual_positives))
            hit_rates_10.append(1.0 if hits_10 > 0 else 0.0)

            # 3. NDCG @ 10
            dcg = 0.0
            idcg = sum(1.0 / math.log2(i + 2) for i in range(min(10, len(actual_positives))))
            for rank, item in enumerate(top_10):
                if item in actual_positives:
                    dcg += 1.0 / math.log2(rank + 2)
            ndcgs_10.append(dcg / idcg if idcg > 0 else 0.0)

            # 4. MAP @ 10 (Mean Average Precision)
            ap = 0.0
            num_hits = 0
            for rank, item in enumerate(top_10):
                if item in actual_positives:
                    num_hits += 1
                    ap += num_hits / (rank + 1)
            maps_10.append(ap / min(10, len(actual_positives)) if actual_positives else 0.0)

            # 5. Diversity (Intra-list Cosine Dissimilarity)
            if len(top_10) > 1 and sim_matrix is not None:
                pairs = 0
                dissim_sum = 0.0
                for i in range(len(top_10)):
                    for j in range(i + 1, len(top_10)):
                        p_a, p_b = top_10[i], top_10[j]
                        if p_a in prod_idx_map and p_b in prod_idx_map:
                            sim = float(sim_matrix[prod_idx_map[p_a], prod_idx_map[p_b]])
                            dissim_sum += (1.0 - sim)
                            pairs += 1
                diversity_scores.append(dissim_sum / pairs if pairs > 0 else 0.5)

        duration = time.time() - start_time
        catalog_coverage = (len(recommended_all_items) / len(all_product_ids)) * 100.0 if all_product_ids else 0.0

        return {
            "model_name": model_name,
            "precision_at_5": round(float(np.mean(precisions_5)), 4) if precisions_5 else 0.0,
            "recall_at_5": round(float(np.mean(recalls_5)), 4) if recalls_5 else 0.0,
            "precision_at_10": round(float(np.mean(precisions_10)), 4) if precisions_10 else 0.0,
            "recall_at_10": round(float(np.mean(recalls_10)), 4) if recalls_10 else 0.0,
            "ndcg_at_10": round(float(np.mean(ndcgs_10)), 4) if ndcgs_10 else 0.0,
            "map_at_10": round(float(np.mean(maps_10)), 4) if maps_10 else 0.0,
            "hit_rate_at_10": round(float(np.mean(hit_rates_10)), 4) if hit_rates_10 else 0.0,
            "catalog_coverage": round(catalog_coverage, 2),
            "diversity_score": round(float(np.mean(diversity_scores)), 4) if diversity_scores else 0.50,
            "duration_sec": round(duration, 3)
        }

    def run_benchmark(self, db: Session) -> List[Dict[str, float]]:
        """
        Runs comprehensive benchmark comparing:
        1. Random Baseline
        2. Popularity Baseline
        3. Content-Based Only
        4. Collaborative Filtering Only (iALS)
        5. Hybrid Engine (RecommendAI)
        """
        random.seed(settings.RANDOM_SEED)
        np.random.seed(settings.RANDOM_SEED)

        # 1. Fetch raw data
        products = db.query(Product).all()
        interactions = db.query(Interaction).all()
        
        all_pids = [p.id for p in products]
        prod_data = [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "category_id": p.category_id,
                "category_name": p.category.name if p.category else "",
                "subcategory": p.subcategory,
                "brand": p.brand,
                "price": p.price,
                "rating": p.rating,
                "rating_count": p.rating_count,
                "stock": p.stock,
                "tags": p.tags,
                "is_active": p.is_active
            }
            for p in products
        ]
        inter_data = [
            {
                "user_id": i.user_id,
                "product_id": i.product_id,
                "interaction_type": i.interaction_type,
                "implicit_weight": i.implicit_weight,
                "created_at": i.created_at
            }
            for i in interactions
        ]

        # 2. Split train/test
        train_inters, test_positives = self.temporal_split(inter_data, test_ratio=0.20)

        # 3. Train models on train split
        cb = ContentBasedRecommender()
        cb.fit(prod_data)

        cf = CollaborativeRecommender()
        cf.fit(train_inters)

        pop = PopularityRecommender()
        pop.fit(train_inters, prod_data)

        hybrid = HybridRecommender(content_model=cb, collab_model=cf, pop_model=pop)

        # Train inter lookup by user
        train_user_inters = defaultdict(list)
        for i in train_inters:
            uid = i.get("user_id")
            if uid:
                train_user_inters[uid].append((i["product_id"], i["implicit_weight"]))

        sim_mat = cb.item_similarity_matrix
        idx_map = cb.product_index_map

        # 4. Define Predict Functions for Each Model
        # (A) Random Baseline
        def predict_random(uid, pool, top_k):
            shuffled = pool.copy()
            random.shuffle(shuffled)
            return shuffled[:top_k]

        # (B) Popularity Baseline
        def predict_pop(uid, pool, top_k):
            scores = pop.predict_item_scores(pool)
            return sorted(pool, key=lambda x: scores.get(x, 0.0), reverse=True)[:top_k]

        # (C) Content-Based Only
        def predict_content(uid, pool, top_k):
            history = train_user_inters.get(uid, [])
            scores = cb.predict_user_scores(history, pool)
            return sorted(pool, key=lambda x: scores.get(x, 0.0), reverse=True)[:top_k]

        # (D) Collaborative Filtering Only
        def predict_collab(uid, pool, top_k):
            scores = cf.predict_user_scores(uid, pool)
            return sorted(pool, key=lambda x: scores.get(x, 0.0), reverse=True)[:top_k]

        # (E) Hybrid Model
        def predict_hybrid(uid, pool, top_k):
            history = train_user_inters.get(uid, [])
            recs = hybrid.recommend(
                user_id=uid,
                user_interactions=history,
                all_product_metadata={p["id"]: p for p in prod_data},
                top_k=top_k
            )
            return [r["product_id"] for r in recs]

        # 5. Run Evaluations
        benchmarks = [
            ("Random Baseline", predict_random),
            ("Popularity Baseline", predict_pop),
            ("Content-Based (TF-IDF)", predict_content),
            ("Collaborative (iALS)", predict_collab),
            ("RecommendAI Hybrid", predict_hybrid)
        ]

        results = []
        for name, fn in benchmarks:
            m = self.evaluate_model(name, fn, test_positives, all_pids, sim_mat, idx_map)
            results.append(m)

            # Persist to database
            metric_record = ModelMetrics(
                model_version="v1.0",
                model_name=name,
                precision_at_5=m["precision_at_5"],
                recall_at_5=m["recall_at_5"],
                precision_at_10=m["precision_at_10"],
                recall_at_10=m["recall_at_10"],
                ndcg_at_10=m["ndcg_at_10"],
                map_at_10=m["map_at_10"],
                hit_rate_at_10=m["hit_rate_at_10"],
                catalog_coverage=m["catalog_coverage"],
                diversity_score=m["diversity_score"],
                training_sample_count=len(train_inters),
                training_duration_sec=m["duration_sec"]
            )
            db.add(metric_record)

        db.commit()
        return results
