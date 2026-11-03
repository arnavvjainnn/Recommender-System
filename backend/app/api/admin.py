from typing import List, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.models.db_models import User, Product, Order, Interaction, Category, ModelMetrics
from app.api.auth import require_admin
from app.schemas.pydantic_models import (
    AnalyticsOverviewResponse, ModelMetricsResponse, RetrainRequest, RetrainStatusResponse
)
from app.recommendation.manager import recommendation_manager
from app.recommendation.evaluator import RecSysEvaluator

router = APIRouter(prefix="/admin", tags=["Admin & Model Operations"])

@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    total_interactions = db.query(Interaction).count()

    # Interaction breakdown
    inter_breakdown_raw = (
        db.query(Interaction.interaction_type, func.count(Interaction.id))
        .group_by(Interaction.interaction_type)
        .all()
    )
    breakdown_map = {t: c for t, c in inter_breakdown_raw}

    # Top selling categories by interaction count
    cat_stats = (
        db.query(Category.name, func.count(Interaction.id))
        .join(Product, Product.category_id == Category.id)
        .join(Interaction, Interaction.product_id == Product.id)
        .group_by(Category.name)
        .order_by(func.count(Interaction.id).desc())
        .limit(6)
        .all()
    )
    top_categories = [{"category": name, "interactions": count} for name, count in cat_stats]

    return AnalyticsOverviewResponse(
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_interactions=total_interactions,
        active_models=["TF-IDF Content", "iALS Matrix Factorization", "Time-Decayed Popularity", "FP-Growth Bundles", "MMR Hybrid"],
        interaction_breakdown=breakdown_map,
        top_selling_categories=top_categories
    )

@router.get("/model-metrics", response_model=List[ModelMetricsResponse])
def get_model_metrics(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns benchmark comparison metrics across Random, Popularity, Content-Based,
    Collaborative, and Hybrid models.
    If no evaluation has run yet, triggers offline benchmark dynamically.
    """
    metrics = db.query(ModelMetrics).order_by(ModelMetrics.created_at.desc()).limit(10).all()
    if not metrics:
        evaluator = RecSysEvaluator()
        evaluator.run_benchmark(db)
        metrics = db.query(ModelMetrics).order_by(ModelMetrics.created_at.desc()).limit(10).all()

    return metrics

def _background_retrain_task(db_session_factory, retrain_config: RetrainRequest):
    db = db_session_factory()
    try:
        recommendation_manager.train(db, weights_config=retrain_config.hybrid_weights)
        evaluator = RecSysEvaluator()
        evaluator.run_benchmark(db)
    finally:
        db.close()

@router.post("/retrain", response_model=RetrainStatusResponse)
def trigger_retraining(
    req: RetrainRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    from app.database.session import SessionLocal
    background_tasks.add_task(_background_retrain_task, SessionLocal, req)

    return RetrainStatusResponse(
        task_id="retrain_task_bg",
        status="TRAINING",
        message="Full multi-model retraining and holdout evaluation launched in background worker."
    )
