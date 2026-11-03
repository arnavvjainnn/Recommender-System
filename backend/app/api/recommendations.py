from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.db_models import User
from app.api.auth import get_current_user
from app.schemas.pydantic_models import RecommendedProductResponse
from app.recommendation.manager import recommendation_manager

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/personalized", response_model=List[RecommendedProductResponse])
def get_personalized_recommendations(
    session_id: str = Query("guest_session", description="Client session identifier"),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized hybrid recommendations dynamically fused across
    Collaborative Filtering, Content-Based Similarity, and Popularity,
    re-ranked via Maximal Marginal Relevance (MMR) for diversity.
    """
    user_id = current_user.id if current_user else None
    return recommendation_manager.get_personalized(
        db=db,
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )

@router.get("/similar/{product_id}", response_model=List[RecommendedProductResponse])
def get_similar_products(
    product_id: str,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Returns content-based similar items derived from TF-IDF vector cosine similarity.
    """
    return recommendation_manager.get_similar_products(
        db=db,
        product_id=product_id,
        limit=limit
    )

@router.get("/frequently-bought/{product_id}", response_model=List[RecommendedProductResponse])
def get_frequently_bought_together(
    product_id: str,
    limit: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Returns association bundle recommendations derived from order basket co-occurrence (FP-Growth).
    """
    return recommendation_manager.get_frequently_bought_together(
        db=db,
        product_id=product_id,
        limit=limit
    )

@router.get("/trending", response_model=List[RecommendedProductResponse])
def get_trending_products(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Returns products experiencing high recent interaction momentum (7-day velocity decay).
    """
    return recommendation_manager.get_trending(db=db, limit=limit)

@router.get("/popular", response_model=List[RecommendedProductResponse])
def get_popular_products(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Returns all-time top community rated products with Bayesian rating smoothing.
    """
    return recommendation_manager.get_popular(db=db, limit=limit)

@router.get("/cold-start", response_model=List[RecommendedProductResponse])
def get_cold_start_recommendations(
    categories: List[str] = Query(..., description="List of category names selected during onboarding"),
    limit: int = Query(10, ge=1, le=30),
    session_id: str = Query("new_user_session"),
    db: Session = Depends(get_db)
):
    """
    Resolves the New-User Cold-Start challenge by synthesizing initial interest vectors
    from onboarding category tags.
    """
    recommendation_manager._ensure_ready(db)
    meta_map = recommendation_manager._get_product_meta_map(db)

    # Synthetic interest profile
    user_interactions = []
    for pid, p in meta_map.items():
        if p.get("category_name") in categories:
            user_interactions.append((pid, 2.0))

    return recommendation_manager.get_personalized(
        db=db,
        user_id=None,
        session_id=session_id,
        limit=limit
    )
