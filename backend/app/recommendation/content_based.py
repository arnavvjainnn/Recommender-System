import json
import numpy as np
from typing import List, Tuple, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from app.config import settings

class ContentBasedRecommender:
    """
    Content-Based Filtering using TF-IDF vectorization over product metadata
    (Title, Category, Subcategory, Brand, Tags, Description) and Cosine Similarity.
    """
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        self.product_ids: List[str] = []
        self.product_index_map: Dict[str, int] = {}
        self.item_similarity_matrix: Optional[np.ndarray] = None

    def fit(self, products: List[dict]):
        """
        Fits TF-IDF vectorizer on composite text representations of all products
        and computes the full pairwise item similarity matrix.
        """
        self.product_ids = [p["id"] for p in products]
        self.product_index_map = {pid: idx for idx, pid in enumerate(self.product_ids)}

        documents = []
        for p in products:
            # Parse tags
            tags = p.get("tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except Exception:
                    tags = []
            tags_str = " ".join(tags) if isinstance(tags, list) else ""

            # Build enriched composite document
            doc = (
                f"{p.get('title', '')} "
                f"{p.get('category_name', '')} "
                f"{p.get('subcategory', '')} "
                f"{p.get('brand', '')} "
                f"{tags_str} "
                f"{p.get('description', '')}"
            )
            documents.append(doc)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            max_features=5000,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        # Compute item-item cosine similarity
        self.item_similarity_matrix = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)

    def get_similar_items(self, product_id: str, top_n: int = 6) -> List[Tuple[str, float]]:
        """
        Returns top-N most similar products for a given product_id based on cosine similarity.
        """
        if self.item_similarity_matrix is None or product_id not in self.product_index_map:
            return []

        idx = self.product_index_map[product_id]
        sim_scores = self.item_similarity_matrix[idx].copy()
        sim_scores[idx] = -1.0  # Exclude self

        top_indices = np.argsort(sim_scores)[::-1][:top_n]
        return [(self.product_ids[i], float(sim_scores[i])) for i in top_indices if sim_scores[i] > 0]

    def predict_user_scores(self, user_interactions: List[Tuple[str, float]], candidate_product_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Constructs user profile vector p_u = sum(r_ui * v_i) and scores candidate products
        via cosine similarity between p_u and candidate item vectors v_j.
        """
        if self.vectorizer is None or self.tfidf_matrix is None or not user_interactions:
            return {}

        # Build weighted user profile vector
        user_vector = np.zeros((1, self.tfidf_matrix.shape[1]))
        total_weight = 0.0

        for pid, weight in user_interactions:
            if pid in self.product_index_map:
                idx = self.product_index_map[pid]
                item_vec = self.tfidf_matrix[idx].toarray()
                user_vector += weight * item_vec
                total_weight += weight

        if total_weight > 0:
            user_vector /= total_weight

        norm = np.linalg.norm(user_vector)
        if norm > 0:
            user_vector /= norm

        # Compute cosine similarity against all or candidate products
        candidate_ids = candidate_product_ids or self.product_ids
        scores = {}
        for pid in candidate_ids:
            if pid in self.product_index_map:
                idx = self.product_index_map[pid]
                item_vec = self.tfidf_matrix[idx].toarray()
                item_norm = np.linalg.norm(item_vec)
                if item_norm > 0:
                    sim = float(np.dot(user_vector, item_vec.T)[0, 0] / item_norm)
                    scores[pid] = max(0.0, sim)
                else:
                    scores[pid] = 0.0

        return scores

    def save(self, filepath=None):
        path = filepath or settings.CONTENT_SIMILARITY_PATH
        joblib.dump({
            "vectorizer": self.vectorizer,
            "tfidf_matrix": self.tfidf_matrix,
            "product_ids": self.product_ids,
            "product_index_map": self.product_index_map,
            "item_similarity_matrix": self.item_similarity_matrix
        }, path)

    def load(self, filepath=None):
        path = filepath or settings.CONTENT_SIMILARITY_PATH
        data = joblib.load(path)
        self.vectorizer = data["vectorizer"]
        self.tfidf_matrix = data["tfidf_matrix"]
        self.product_ids = data["product_ids"]
        self.product_index_map = data["product_index_map"]
        self.item_similarity_matrix = data["item_similarity_matrix"]
