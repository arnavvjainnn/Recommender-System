from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import joblib
from app.config import settings

class AssociationRulesRecommender:
    """
    Market Basket Analysis for 'Frequently Bought Together' bundles.
    Computes Support, Confidence, and Lift metrics over co-occurring basket purchases.
    Uses an efficient in-memory co-occurrence graph with min_support and min_confidence thresholds.
    """
    def __init__(self, min_support: float = 0.01, min_confidence: float = 0.20, min_lift: float = 1.05):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
        # Mapping: antecedent_product_id -> list of (consequent_product_id, support, confidence, lift)
        self.rules: Dict[str, List[Dict[str, float]]] = defaultdict(list)

    def fit(self, orders_data: List[List[str]]):
        """
        Fits association rules on transaction baskets.
        orders_data: List of order baskets, where each basket is a list of product_ids.
        """
        self.rules = defaultdict(list)
        total_transactions = len(orders_data)
        if total_transactions < 2:
            return

        # 1. Calculate individual item frequencies
        item_counts = defaultdict(int)
        pair_counts = defaultdict(int)

        for basket in orders_data:
            unique_items = sorted(list(set(basket)))
            for item in unique_items:
                item_counts[item] += 1
            
            # Co-occurrence pairs
            for i in range(len(unique_items)):
                for j in range(i + 1, len(unique_items)):
                    pair = (unique_items[i], unique_items[j])
                    pair_counts[pair] += 1

        # 2. Derive directional association rules A -> B and B -> A
        for (item_a, item_b), count in pair_counts.items():
            support_ab = count / total_transactions
            if support_ab < self.min_support:
                continue

            support_a = item_counts[item_a] / total_transactions
            support_b = item_counts[item_b] / total_transactions

            # A -> B
            conf_a_to_b = support_ab / support_a if support_a > 0 else 0.0
            lift_a_to_b = conf_a_to_b / support_b if support_b > 0 else 0.0
            if conf_a_to_b >= self.min_confidence and lift_a_to_b >= self.min_lift:
                self.rules[item_a].append({
                    "consequent_id": item_b,
                    "support": round(support_ab, 4),
                    "confidence": round(conf_a_to_b, 4),
                    "lift": round(lift_a_to_b, 4)
                })

            # B -> A
            conf_b_to_a = support_ab / support_b if support_b > 0 else 0.0
            lift_b_to_a = conf_b_to_a / support_a if support_a > 0 else 0.0
            if conf_b_to_a >= self.min_confidence and lift_b_to_a >= self.min_lift:
                self.rules[item_b].append({
                    "consequent_id": item_a,
                    "support": round(support_ab, 4),
                    "confidence": round(conf_b_to_a, 4),
                    "lift": round(lift_b_to_a, 4)
                })

        # Sort rules by highest lift then confidence
        for antecedent in self.rules:
            self.rules[antecedent].sort(key=lambda r: (r["lift"], r["confidence"]), reverse=True)

    def get_frequently_bought_together(self, product_id: str, top_n: int = 4) -> List[Dict[str, float]]:
        """
        Retrieves top bundle add-ons for a given product_id ordered by Lift and Confidence.
        """
        return self.rules.get(product_id, [])[:top_n]

    def save(self, filepath=None):
        path = filepath or settings.ASSOCIATION_RULES_PATH
        joblib.dump({
            "rules": dict(self.rules),
            "min_support": self.min_support,
            "min_confidence": self.min_confidence,
            "min_lift": self.min_lift
        }, path)

    def load(self, filepath=None):
        path = filepath or settings.ASSOCIATION_RULES_PATH
        data = joblib.load(path)
        self.rules = defaultdict(list, data["rules"])
        self.min_support = data["min_support"]
        self.min_confidence = data["min_confidence"]
        self.min_lift = data["min_lift"]
