from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config import settings
from app.database.session import get_db
from app.models.db_models import User, Interaction, Rating, Product, Order, OrderItem
from app.api.auth import get_current_user, require_current_user
from app.schemas.pydantic_models import (
    InteractionCreateRequest, RatingCreateRequest, RatingResponse,
    CheckoutRequest, OrderResponse
)

router = APIRouter(tags=["Interactions & Orders"])

@router.post("/interactions")
def log_interaction(
    req: InteractionCreateRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Asynchronously logs a user interaction event with configured implicit feedback weight.
    Supports both logged-in users and anonymous sessions.
    """
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    weight = settings.EVENT_WEIGHTS.get(req.interaction_type.upper(), 1.0)
    user_id = current_user.id if current_user else None

    interaction = Interaction(
        user_id=user_id,
        session_id=req.session_id,
        product_id=req.product_id,
        interaction_type=req.interaction_type.upper(),
        implicit_weight=weight,
        created_at=datetime.now(timezone.utc)
    )
    db.add(interaction)
    db.commit()

    return {"status": "logged", "weight": weight}

@router.post("/ratings", response_model=RatingResponse)
def submit_rating(
    req: RatingCreateRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update or insert rating
    rating = (
        db.query(Rating)
        .filter(Rating.user_id == current_user.id, Rating.product_id == req.product_id)
        .first()
    )
    if rating:
        rating.rating_value = req.rating_value
        rating.review_text = req.review_text
    else:
        rating = Rating(
            user_id=current_user.id,
            product_id=req.product_id,
            rating_value=req.rating_value,
            review_text=req.review_text
        )
        db.add(rating)

    # Re-calculate product's average rating
    all_ratings = db.query(Rating).filter(Rating.product_id == req.product_id).all()
    count = len(all_ratings)
    avg_score = sum(r.rating_value for r in all_ratings) / count if count > 0 else req.rating_value
    product.rating = round(avg_score, 1)
    product.rating_count = count

    # Also log as an implicit interaction event
    interaction = Interaction(
        user_id=current_user.id,
        session_id=f"session_{current_user.id[:8]}",
        product_id=req.product_id,
        interaction_type="RATING",
        implicit_weight=settings.EVENT_WEIGHTS.get("RATING", 6.0)
    )
    db.add(interaction)
    db.commit()

    return RatingResponse(
        id=rating.id,
        user_id=rating.user_id,
        product_id=rating.product_id,
        rating_value=rating.rating_value,
        review_text=rating.review_text,
        created_at=rating.created_at
    )

@router.post("/cart/checkout", response_model=OrderResponse)
def process_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    if not req.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")

    total_amount = 0.0
    order_items_to_create = []

    for item in req.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            continue
        subtotal = product.price * item.quantity
        total_amount += subtotal
        order_items_to_create.append((product, item.quantity, subtotal))

        # Log purchase interaction
        inter = Interaction(
            user_id=current_user.id,
            session_id=f"session_{current_user.id[:8]}",
            product_id=product.id,
            interaction_type="PURCHASE",
            implicit_weight=settings.EVENT_WEIGHTS.get("PURCHASE", 8.0)
        )
        db.add(inter)

    order = Order(
        user_id=current_user.id,
        total_amount=round(total_amount, 2),
        status="COMPLETED",
        shipping_address=req.shipping_address or "Campus Tech Park"
    )
    db.add(order)
    db.flush()

    for prod, qty, subtotal in order_items_to_create:
        oi = OrderItem(
            order_id=order.id,
            product_id=prod.id,
            quantity=qty,
            unit_price=prod.price,
            subtotal=round(subtotal, 2)
        )
        db.add(oi)

    db.commit()

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        item_count=len(order_items_to_create)
    )
