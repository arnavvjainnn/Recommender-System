"""
RecommendAI — Standalone Offline Evaluation Benchmark Script
Executes Leave-Last-20% temporal holdout splitting with 1:99 negative item sampling
and computes Precision@5, Precision@10, Recall@10, NDCG@10, MAP@10, HitRate@10,
Catalog Coverage, and Inter-List Diversity across all baseline and proposed models.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from app.database.session import SessionLocal, init_db
from app.database.seed_data import seed_database
from app.models.db_models import Product
from app.recommendation.evaluator import RecSysEvaluator

def main():
    print("=" * 80)
    print("RECOMMENDAI: Offline Information Retrieval (IR) Benchmark Suite")
    print("Protocol: Temporal Holdout (80/20) + 1:99 Negative Item Sampling")
    print("=" * 80)

    init_db()
    db = SessionLocal()
    try:
        count = db.query(Product).count()
        if count == 0:
            print("Seeding database first...")
            seed_database(db)

        evaluator = RecSysEvaluator()
        results = evaluator.run_benchmark(db)

        print("\n" + "-" * 105)
        print(f"{'Model Architecture':<26} | {'P@5':<7} | {'R@5':<7} | {'NDCG@10':<8} | {'MAP@10':<7} | {'HR@10':<7} | {'Coverage':<9} | {'Diversity':<9}")
        print("-" * 105)
        for r in results:
            print(
                f"{r['model_name']:<26} | "
                f"{r['precision_at_5']*100:>5.1f}% | "
                f"{r['recall_at_5']*100:>5.1f}% | "
                f"{r['ndcg_at_10']:>8.3f} | "
                f"{r['map_at_10']:>7.3f} | "
                f"{r['hit_rate_at_10']*100:>5.1f}% | "
                f"{r['catalog_coverage']:>7.1f}% | "
                f"{r['diversity_score']:>9.3f}"
            )
        print("-" * 105)
        print("\nAll evaluation records persisted to 'model_metrics' table for live Admin Telemetry display.\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
