import math
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import joblib
from app.config import settings

class PopularityRecommender:
    """
    Time-Decayed Popularity & Trending Recommender.
    Combines Bayesian smoothed rating with exponentially decayed interaction volume
    and 7-day velocity tracking to reward active momentum.
    """
    def __init__(self, half_life_days: float = 30.0):
        self.half_life_days = half_life_days
        self.decay_lambda = math.log(2.0) / half_life_days
        self.item_popularity_scores: Dict[str, float] = {}
        self.item_trending_scores: Dict[str, float] = {}

    def fit(self, interactions: List[dict], products: List[dict]):
        """
        Fits popularity and trending scores over all historical interactions.
        """
        now = datetime.now(timezone.utc)
        product_event_weights: Dict[str, float] = {p["id"]: 0.0 for p in products}
        product_recent_weights: Dict[str, float] = {p["id"]: 0.0 for p in products}
        
        # 1. Accumulate decayed interaction weights
        for inter in interactions:
            pid = inter.get("product_id")
            if pid not in product_event_weights:
                continue

            created_at = inter.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            delta_days = (now - created_at).total_seconds() / 86400.0 if created_at else 0.0
            decay_factor = math.exp(-self.decay_lambda * max(0.0, delta_days))
            weight = float(inter.get("implicit_weight", 1.0)) * decay_factor

            product_event_weights[pid] += weight

            # Track velocity (interactions within last 7 days)
            if delta_days <= 7.0:
                product_recent_weights[pid] += weight

        # 2. Bayesian smoothed rating
        # S_bayes = (C * m + sum(ratings)) / (C + n)
        C = 10.0  # Confidence weight
        global_avg_rating = 4.5
        
        raw_pop_scores = {}
        raw_trend_scores = {}

        for p in products:
            pid = p["id"]
            rating = float(p.get("rating", 4.0))
            count = int(p.get("rating_count", 0))
            bayes_rating = (C * global_avg_rating + rating * count) / (C + count)

            event_score = product_event_weights.get(pid, 0.0)
            recent_score = product_recent_weights.get(pid, 0.0)

            # Composite Popularity Score: 70% interactions volume + 30% Bayesian rating
            raw_pop_scores[pid] = math.log1p(event_score) * 0.70 + (bayes_rating / 5.0) * 0.30
            # Trending Score: Momentum velocity within last 7 days
            raw_trend_scores[pid] = math.log1p(recent_score * 2.0) + (bayes_rating / 5.0) * 0.20

        # Min-max normalization
        self.item_popularity_scores = self._normalize_scores(raw_pop_scores)
        self.item_trending_scores = self._normalize_scores(raw_trend_scores)

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        vals = list(scores.values())
        min_v, max_v = min(vals), max(vals)
        spread = max_v - min_v
        if spread <= 1e-6:
            return {k: 0.5 for k in scores}
        return {k: float((v - min_v) / spread) for k, v in scores.items()}

    def get_top_popular(self, top_n: int = 10) -> List[Tuple[str, float]]:
        sorted_items = sorted(self.item_popularity_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_n]

    def get_top_trending(self, top_n: int = 10) -> List[Tuple[str, float]]:
        sorted_items = sorted(self.item_trending_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:top_n]

    def predict_item_scores(self, candidate_item_ids: Optional[List[str]] = None) -> Dict[str, float]:
        if candidate_item_ids is None:
            return self.item_popularity_scores.copy()
        return {pid: self.item_popularity_scores.get(pid, 0.0) for pid in candidate_item_ids}

    def save(self, filepath=None):
        path = filepath or settings.POPULARITY_MODEL_PATH
        joblib.dump({
            "half_life_days": self.half_life_days,
            "item_popularity_scores": self.item_popularity_scores,
            "item_trending_scores": self.item_trending_scores
        }, path)

    def load(self, filepath=None):
        path = filepath or settings.POPULARITY_MODEL_PATH
        data = joblib.load(path)
        self.half_life_days = data["half_life_days"]
        self.item_popularity_scores = data["item_popularity_scores"]
        self.item_trending_scores = data["item_trending_scores"]
