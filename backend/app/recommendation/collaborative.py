import numpy as np
import scipy.sparse as sp
from typing import List, Dict, Tuple, Optional
import joblib
from app.config import settings

class CollaborativeRecommender:
    """
    Implicit Feedback Matrix Factorization using Alternating Least Squares (iALS)
    (Hu, Koren, Volinsky formulation).
    Minimizes: sum_u,i c_ui (p_ui - x_u^T y_i)^2 + lambda (||x_u||^2 + ||y_i||^2)
    where c_ui = 1 + alpha * r_ui, and p_ui = 1 if r_ui > 0 else 0.
    """
    def __init__(self, n_factors: int = 32, regularization: float = 0.05, alpha: float = 40.0, iterations: int = 15):
        self.n_factors = n_factors
        self.regularization = regularization
        self.alpha = alpha
        self.iterations = iterations
        
        self.user_ids: List[str] = []
        self.item_ids: List[str] = []
        self.user_index_map: Dict[str, int] = {}
        self.item_index_map: Dict[str, int] = {}
        
        self.user_factors: Optional[np.ndarray] = None  # Shape: (n_users, n_factors)
        self.item_factors: Optional[np.ndarray] = None  # Shape: (n_items, n_factors)

    def fit(self, interactions: List[dict]):
        """
        Builds the user-item interaction matrix and fits the latent factors via iALS.
        interactions: List of dicts with keys 'user_id', 'product_id', 'implicit_weight'.
        """
        if not interactions:
            return

        self.user_ids = sorted(list({i["user_id"] for i in interactions if i.get("user_id")}))
        self.item_ids = sorted(list({i["product_id"] for i in interactions if i.get("product_id")}))
        
        self.user_index_map = {uid: idx for idx, uid in enumerate(self.user_ids)}
        self.item_index_map = {iid: idx for idx, iid in enumerate(self.item_ids)}
        
        n_users = len(self.user_ids)
        n_items = len(self.item_ids)

        if n_users == 0 or n_items == 0:
            return

        # Build sparse interaction rating matrix R
        rows, cols, data = [], [], []
        for inter in interactions:
            uid = inter.get("user_id")
            pid = inter.get("product_id")
            if uid in self.user_index_map and pid in self.item_index_map:
                rows.append(self.user_index_map[uid])
                cols.append(self.item_index_map[pid])
                data.append(float(inter.get("implicit_weight", 1.0)))

        R = sp.csr_matrix((data, (rows, cols)), shape=(n_users, n_items))

        # Check if C-accelerated 'implicit' library is installed and usable
        try:
            import implicit
            als_model = implicit.als.AlternatingLeastSquares(
                factors=self.n_factors,
                regularization=self.regularization,
                iterations=self.iterations,
                random_state=settings.RANDOM_SEED
            )
            # implicit library expects confidence matrix C - I
            als_model.fit(R * self.alpha, show_progress=False)
            self.user_factors = als_model.user_factors
            self.item_factors = als_model.item_factors
            return
        except Exception:
            # Vectorized Pure NumPy / SciPy iALS Solver Fallback
            self._fit_numpy_ials(R)

    def _fit_numpy_ials(self, R: sp.csr_matrix):
        """
        Vectorized Pure NumPy / SciPy implementation of the Hu, Koren, Volinsky iALS algorithm.
        Guarantees 100% platform portability without C-compilation dependencies.
        """
        n_users, n_items = R.shape
        np.random.seed(settings.RANDOM_SEED)
        
        # Initialize factors with small normal random values
        self.user_factors = np.random.normal(0, 0.01, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.01, (n_items, self.n_factors))
        
        lambda_eye = self.regularization * np.eye(self.n_factors)

        for _ in range(self.iterations):
            # 1. Update user factors X: (Y^T Y + Y^T (C_u - I) Y + lambda I)^(-1) Y^T C_u p_u
            YtY = self.item_factors.T @ self.item_factors
            for u in range(n_users):
                r_u = R.getrow(u)
                item_indices = r_u.indices
                if len(item_indices) == 0:
                    continue
                
                weights = r_u.data
                Cu_minus_I = self.alpha * weights
                Y_u = self.item_factors[item_indices]
                
                # A_u = YtY + Y_u^T diag(Cu - 1) Y_u + lambda I
                A_u = YtY + (Y_u.T * Cu_minus_I) @ Y_u + lambda_eye
                # b_u = Y_u^T (Cu p_u) where p_u=1 for observed items, Cu = 1 + alpha*r_ui
                b_u = Y_u.T @ (1.0 + Cu_minus_I)
                self.user_factors[u] = np.linalg.solve(A_u, b_u)

            # 2. Update item factors Y: (X^T X + X^T (C_i - I) X + lambda I)^(-1) X^T C_i p_i
            XtX = self.user_factors.T @ self.user_factors
            R_csc = R.tocsc()
            for i in range(n_items):
                r_i = R_csc.getcol(i)
                user_indices = r_i.indices
                if len(user_indices) == 0:
                    continue
                
                weights = r_i.data
                Ci_minus_I = self.alpha * weights
                X_i = self.user_factors[user_indices]
                
                A_i = XtX + (X_i.T * Ci_minus_I) @ X_i + lambda_eye
                b_i = X_i.T @ (1.0 + Ci_minus_I)
                self.item_factors[i] = np.linalg.solve(A_i, b_i)

    def predict_user_scores(self, user_id: str, candidate_item_ids: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Computes predicted preference scores p_ui = x_u^T y_i for all candidate items.
        """
        if self.user_factors is None or self.item_factors is None or user_id not in self.user_index_map:
            return {}

        u_idx = self.user_index_map[user_id]
        u_factor = self.user_factors[u_idx]

        candidates = candidate_item_ids or self.item_ids
        scores = {}
        for pid in candidates:
            if pid in self.item_index_map:
                i_idx = self.item_index_map[pid]
                i_factor = self.item_factors[i_idx]
                score = float(np.dot(u_factor, i_factor))
                scores[pid] = max(0.0, score)
            else:
                scores[pid] = 0.0

        return scores

    def save(self, filepath=None):
        path = filepath or settings.COLLABORATIVE_MODEL_PATH
        joblib.dump({
            "n_factors": self.n_factors,
            "regularization": self.regularization,
            "alpha": self.alpha,
            "user_ids": self.user_ids,
            "item_ids": self.item_ids,
            "user_index_map": self.user_index_map,
            "item_index_map": self.item_index_map,
            "user_factors": self.user_factors,
            "item_factors": self.item_factors
        }, path)

    def load(self, filepath=None):
        path = filepath or settings.COLLABORATIVE_MODEL_PATH
        data = joblib.load(path)
        self.n_factors = data["n_factors"]
        self.regularization = data["regularization"]
        self.alpha = data["alpha"]
        self.user_ids = data["user_ids"]
        self.item_ids = data["item_ids"]
        self.user_index_map = data["user_index_map"]
        self.item_index_map = data["item_index_map"]
        self.user_factors = data["user_factors"]
        self.item_factors = data["item_factors"]
