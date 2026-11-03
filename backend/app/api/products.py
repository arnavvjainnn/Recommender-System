import json
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database.session import get_db
from app.models.db_models import Product, Category
from app.schemas.pydantic_models import (
    ProductResponse, PaginatedProductsResponse, CategoryResponse, ProductCreateRequest
)
from app.recommendation.manager import recommendation_manager

router = APIRouter(prefix="/products", tags=["Products"])

def format_product_response(p: Product) -> ProductResponse:
    tags = []
    if isinstance(p.tags, str):
        try:
            tags = json.loads(p.tags)
        except Exception:
            tags = []
    elif isinstance(p.tags, list):
        tags = p.tags

    return ProductResponse(
        id=p.id,
        title=p.title,
        description=p.description,
        category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        subcategory=p.subcategory,
        brand=p.brand,
        price=p.price,
        discount_percent=p.discount_percent,
        rating=p.rating,
        rating_count=p.rating_count,
        stock=p.stock,
        image_url=p.image_url,
        tags=tags,
        is_active=p.is_active,
        created_at=p.created_at
    )

@router.get("", response_model=PaginatedProductsResponse)
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    category_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = Query("popular", description="popular, price_asc, price_desc, rating, newest"),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort_by == "rating":
        query = query.order_by(desc(Product.rating))
    elif sort_by == "newest":
        query = query.order_by(desc(Product.created_at))
    else:
        query = query.order_by(desc(Product.rating_count), desc(Product.rating))

    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    return PaginatedProductsResponse(
        items=[format_product_response(p) for p in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/search", response_model=List[ProductResponse])
def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search using TF-IDF cosine similarity over the product catalog if vectors exist,
    with SQL ILIKE fallback.
    """
    recommendation_manager._ensure_ready(db)
    
    # Try TF-IDF vector search
    if recommendation_manager.content_model.vectorizer is not None:
        try:
            query_vec = recommendation_manager.content_model.vectorizer.transform([q])
            tfidf_mat = recommendation_manager.content_model.tfidf_matrix
            sims = (query_vec @ tfidf_mat.T).toarray()[0]
            
            top_indices = [i for i in sims.argsort()[::-1] if sims[i] > 0.05][:limit]
            if top_indices:
                matched_pids = [recommendation_manager.content_model.product_ids[i] for i in top_indices]
                products = db.query(Product).filter(Product.id.in_(matched_pids)).all()
                # Sort according to similarity rank
                p_dict = {p.id: p for p in products}
                return [format_product_response(p_dict[pid]) for pid in matched_pids if pid in p_dict]
        except Exception:
            pass

    # Fallback to text matching
    query_pattern = f"%{q}%"
    products = (
        db.query(Product)
        .filter(
            Product.is_active == True,
            or_(
                Product.title.ilike(query_pattern),
                Product.description.ilike(query_pattern),
                Product.brand.ilike(query_pattern),
                Product.tags.ilike(query_pattern)
            )
        )
        .limit(limit)
        .all()
    )
    return [format_product_response(p) for p in products]

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return format_product_response(product)
