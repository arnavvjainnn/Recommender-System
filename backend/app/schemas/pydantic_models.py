from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ----------------- User & Auth Schemas -----------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    age: Optional[int] = Field(None, ge=12, le=120)
    gender: Optional[str] = None
    location: Optional[str] = None
    preferred_categories: Optional[List[str]] = Field(default_factory=list)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    preferred_categories: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True

class PreferencesUpdateRequest(BaseModel):
    categories: List[str] = Field(..., min_length=1)
    min_price: Optional[float] = 0.0
    max_price: Optional[float] = None

# ----------------- Product & Category Schemas -----------------
class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    title: str
    description: str
    category_id: int
    subcategory: Optional[str] = None
    brand: str
    price: float
    discount_percent: float = 0.0
    stock: int = 100
    image_url: str
    tags: List[str] = []

class ProductCreateRequest(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str
    rating: float = 0.0
    rating_count: int = 0
    is_active: bool = True
    category_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int

# ----------------- Interaction & Rating Schemas -----------------
class InteractionCreateRequest(BaseModel):
    product_id: str
    interaction_type: str = Field(..., description="VIEW, CLICK, LIKE, ADD_TO_CART, PURCHASE, RATING")
    session_id: str = Field(..., min_length=1)

class RatingCreateRequest(BaseModel):
    product_id: str
    rating_value: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = None

class RatingResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    rating_value: float
    review_text: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Recommendation Schemas -----------------
class RecommendationExplanation(BaseModel):
    primary_factor: str  # "CONTENT_SIMILARITY", "COLLABORATIVE_FILTERING", "POPULAR_TRENDING", "FREQUENT_BUNDLE", "CATEGORY_INTEREST"
    reason_text: str
    content_score: float = 0.0
    collaborative_score: float = 0.0
    popularity_score: float = 0.0
    final_score: float = 0.0

class RecommendedProductResponse(BaseModel):
    product: ProductResponse
    score: float
    explanation: RecommendationExplanation

class ColdStartRequest(BaseModel):
    preferred_categories: List[str]
    session_id: str
    limit: int = 10

class HybridWeightsConfig(BaseModel):
    weight_collaborative: float = Field(0.45, ge=0.0, le=1.0)
    weight_content: float = Field(0.35, ge=0.0, le=1.0)
    weight_popularity: float = Field(0.20, ge=0.0, le=1.0)
    mmr_diversity_lambda: float = Field(0.75, ge=0.0, le=1.0)

# ----------------- Order Schemas -----------------
class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(1, ge=1)

class CheckoutRequest(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = "Demo Campus Shipping Address"

class OrderResponse(BaseModel):
    id: str
    user_id: str
    total_amount: float
    status: str
    created_at: datetime
    item_count: int

# ----------------- Admin & Model Metrics Schemas -----------------
class AnalyticsOverviewResponse(BaseModel):
    total_users: int
    total_products: int
    total_orders: int
    total_interactions: int
    active_models: List[str]
    interaction_breakdown: Dict[str, int]
    top_selling_categories: List[Dict[str, Any]]

class ModelMetricsResponse(BaseModel):
    id: str
    model_version: str
    model_name: str
    precision_at_5: float
    recall_at_5: float
    precision_at_10: float
    recall_at_10: float
    ndcg_at_10: float
    map_at_10: float
    hit_rate_at_10: float
    catalog_coverage: float
    diversity_score: float
    training_sample_count: int
    training_duration_sec: float
    created_at: datetime

    class Config:
        from_attributes = True

class RetrainRequest(BaseModel):
    epochs: int = 15
    factors: int = 32
    regularization: float = 0.05
    hybrid_weights: Optional[HybridWeightsConfig] = None

class RetrainStatusResponse(BaseModel):
    task_id: str
    status: str  # "PENDING", "TRAINING", "COMPLETED", "FAILED"
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Optional[Dict[str, float]] = None
