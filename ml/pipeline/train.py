"""
RecommendAI — Standalone Offline Training Pipeline Script
Executes full ingestion, feature extraction, TF-IDF vectorization,
Implicit ALS matrix factorization, time-decayed popularity weighting,
and FP-Growth association basket mining.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from app.database.session import SessionLocal, init_db
from app.database.seed_data import seed_database
from app.models.db_models import Product
from app.recommendation.manager import recommendation_manager

def main():
    print("=" * 60)
    print("RECOMMENDAI: Offline Model Training & Serialization Pipeline")
    print("=" * 60)

    init_db()
    db = SessionLocal()
    try:
        count = db.query(Product).count()
        if count == 0:
            print("Database empty. Seeding catalog and telemetry...")
            res = seed_database(db)
            print(f"Seeded: {res}")

        print("Fitting Content-Based, iALS, Popularity & FP-Growth models...")
        train_res = recommendation_manager.train(db)
        print(f"Training successfully completed:")
        print(f" - Indexed Products: {train_res['products_indexed']}")
        print(f" - Trained Interactions: {train_res['interactions_trained']}")
        print(f" - Mined Order Baskets: {train_res['baskets_mined']}")
        print("Model artifacts successfully saved to ml/saved_models/")
    finally:
        db.close()

if __name__ == "__main__":
    main()
