import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import init_db, SessionLocal
from app.database.seed_data import seed_database
from app.models.db_models import Product
from app.recommendation.manager import recommendation_manager
from app.recommendation.evaluator import RecSysEvaluator

from app.api import auth, products, interactions, recommendations, admin

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("recommendai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event:
    1. Initializes database tables if missing.
    2. Seeds catalog, user personas, and interaction telemetry if database is empty.
    3. Fits and verifies initial ML models (Content, iALS, Popularity, FP-Growth).
    """
    logger.info("Initializing RecommendAI Application & Database...")
    init_db()

    db = SessionLocal()
    try:
        # Check if database needs seeding
        product_count = db.query(Product).count()
        if product_count == 0:
            logger.info("Database is empty. Automatically executing seed pipeline...")
            seed_res = seed_database(db)
            logger.info(f"Seeding completed: {seed_res}")
            
            # Train models and run baseline evaluation benchmark
            logger.info("Fitting recommendation models on seeded telemetry...")
            recommendation_manager.train(db)
            logger.info("Running offline holdout benchmark...")
            evaluator = RecSysEvaluator()
            evaluator.run_benchmark(db)
            logger.info("Initial holdout evaluation complete.")
        else:
            # Ensure in-memory engines are warmed up
            logger.info(f"Database already populated ({product_count} products). Warming ML models...")
            recommendation_manager._ensure_ready(db)
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}", exc_info=True)
    finally:
        db.close()

    yield
    logger.info("RecommendAI backend shutting down.")

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent E-Commerce Recommendation Engine demonstrating Content-Based, Implicit Collaborative Filtering, Time-Decayed Popularity, and MMR Diversity Re-ranking.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local React dev servers on any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root API Router
api_router = APIRouter(prefix=settings.API_V1_STR)
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(interactions.router)
api_router.include_router(recommendations.router)
api_router.include_router(admin.router)

app.include_router(api_router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }
