import pytest
import numpy as np
from app.recommendation.content_based import ContentBasedRecommender
from app.recommendation.collaborative import CollaborativeRecommender
from app.recommendation.popularity import PopularityRecommender
from app.recommendation.association_rules import AssociationRulesRecommender
from app.recommendation.hybrid import HybridRecommender

SAMPLE_PRODUCTS = [
    {
        "id": "p1",
        "title": "Wireless Mechanical Gaming Keyboard",
        "description": "Ultra responsive RGB switches for esports competitive gaming.",
        "category_name": "Gaming",
        "subcategory": "Keyboards",
        "brand": "SteelSeries",
        "price": 199.99,
        "rating": 4.8,
        "rating_count": 100,
        "stock": 50,
        "tags": ["gaming", "mechanical", "wireless"],
        "is_active": True
    },
    {
        "id": "p2",
        "title": "Esports Lightweight Wireless Gaming Mouse",
        "description": "Ultra lightweight 63g sensor designed for competitive gaming.",
        "category_name": "Gaming",
        "subcategory": "Mice",
        "brand": "Razer",
        "price": 149.99,
        "rating": 4.7,
        "rating_count": 80,
        "stock": 40,
        "tags": ["gaming", "mouse", "wireless"],
        "is_active": True
    },
    {
        "id": "p3",
        "title": "Studio Reference Audiophile Headphones",
        "description": "High resolution open-back acoustic monitoring for mixing and mastering.",
        "category_name": "Audio",
        "subcategory": "Studio",
        "brand": "Sennheiser",
        "price": 499.99,
        "rating": 4.9,
        "rating_count": 60,
        "stock": 25,
        "tags": ["audio", "studio", "headphones", "audiophile"],
        "is_active": True
    }
]

SAMPLE_INTERACTIONS = [
    {"user_id": "u1", "product_id": "p1", "implicit_weight": 5.0},
    {"user_id": "u1", "product_id": "p2", "implicit_weight": 8.0},
    {"user_id": "u2", "product_id": "p3", "implicit_weight": 5.0},
    {"user_id": "u3", "product_id": "p1", "implicit_weight": 3.0},
    {"user_id": "u3", "product_id": "p2", "implicit_weight": 8.0},
]

def test_content_based_recommender():
    cb = ContentBasedRecommender()
    cb.fit(SAMPLE_PRODUCTS)
    
    assert cb.vectorizer is not None
    assert len(cb.product_ids) == 3

    # Keyboard (p1) should be much closer to mouse (p2) than studio headphones (p3)
    similar_to_p1 = dict(cb.get_similar_items("p1", top_n=2))
    assert "p2" in similar_to_p1
    assert similar_to_p1["p2"] > similar_to_p1.get("p3", 0.0)

def test_collaborative_recommender():
    cf = CollaborativeRecommender(n_factors=8, iterations=10)
    cf.fit(SAMPLE_INTERACTIONS)
    
    assert cf.user_factors is not None
    assert cf.item_factors is not None
    
    # Predict scores for user u1
    scores = cf.predict_user_scores("u1")
    assert isinstance(scores, dict)
    assert len(scores) > 0

def test_popularity_recommender():
    pop = PopularityRecommender()
    pop.fit(SAMPLE_INTERACTIONS, SAMPLE_PRODUCTS)
    
    top_items = pop.get_top_popular(top_n=3)
    assert len(top_items) > 0
    # Items with high purchase weights (p1 and p2) should rank high
    top_pids = [item[0] for item in top_items]
    assert "p2" in top_pids or "p1" in top_pids

def test_association_rules():
    assoc = AssociationRulesRecommender(min_support=0.1, min_confidence=0.1, min_lift=1.0)
    baskets = [
        ["p1", "p2"],
        ["p1", "p2"],
        ["p1", "p3"],
        ["p1", "p2"]
    ]
    assoc.fit(baskets)
    
    bundles = assoc.get_frequently_bought_together("p1")
    assert len(bundles) > 0
    assert bundles[0]["consequent_id"] == "p2"
    assert bundles[0]["lift"] >= 1.0

def test_hybrid_recommender_and_mmr():
    cb = ContentBasedRecommender()
    cb.fit(SAMPLE_PRODUCTS)

    cf = CollaborativeRecommender(n_factors=8, iterations=10)
    cf.fit(SAMPLE_INTERACTIONS)

    pop = PopularityRecommender()
    pop.fit(SAMPLE_INTERACTIONS, SAMPLE_PRODUCTS)

    hybrid = HybridRecommender(content_model=cb, collab_model=cf, pop_model=pop, mmr_lambda=0.7)
    
    meta = {p["id"]: p for p in SAMPLE_PRODUCTS}
    recs = hybrid.recommend(
        user_id="u1",
        user_interactions=[("p1", 5.0)],
        all_product_metadata=meta,
        top_k=2
    )

    assert len(recs) <= 2
    assert "score" in recs[0]
    assert "breakdown" in recs[0]
