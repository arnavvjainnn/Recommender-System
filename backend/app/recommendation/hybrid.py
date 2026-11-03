import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from app.config import settings
from app.recommendation.content_based import ContentBasedRecommender
from app.recommendation.collaborative import CollaborativeRecommender
from app.recommendation.popularity import PopularityRecommender

class HybridRecommender:
    """
    Two-stage Hybrid Recommendation Engine.
    Combines Collaborative Filtering, Content-Based Similarity, and Popularity
    with Min-Max normalization, business constraints, and Maximal Marginal Relevance (MMR)
    for category and item diversity.
    """
    def __init__(
        self,
        content_model: ContentBasedRecommender,
        collab_model: CollaborativeRecommender,
        pop_model: PopularityRecommender,
        weight_collab: float = 0.45,
        weight_content: float = 0.35,
        weight_pop: float = 0.20,
        mmr_lambda: float = 0.75
    ):
        self.content_model = content_model
        self.collab_model = collab_model
        self.pop_model = pop_model
        self.w_collab = weight_collab
        self.w_content = weight_content
        self.w_pop = weight_pop
        self.mmr_lambda = mmr_lambda

    def _min_max_scale(self, score_dict: Dict[str, float]) -> Dict[str, float]:
        if not score_dict:
            return {}
        vals = list(score_dict.values())
        min_v = min(vals)
        max_v = max(vals)
        spread = max_v - min_v
        if spread <= 1e-6:
            return {k: 0.5 for k in score_dict}
        return {k: float((v - min_v) / spread) for k, v in score_dict.items()}

    def recommend(
        self,
        user_id: Optional[str],
        user_interactions: List[Tuple[str, float]],
        user_preferences: Optional[List[str]] = None,
        all_product_metadata: Optional[Dict[str, dict]] = None,
        excluded_product_ids: Optional[Set[str]] = None,
        top_k: int = 10
    ) -> List[Dict[str, any]]:
        """
        Executes candidate generation, normalization, hybrid fusion, and MMR re-ranking.
        Returns top_k items with score breakdown and explanation signals.
        """
        all_pids = list(all_product_metadata.keys()) if all_product_metadata else self.content_model.product_ids
        excluded = excluded_product_ids or set()

        # Filter out invalid, inactive, or zero-stock products
        valid_candidates = []
        for pid in all_pids:
            if pid in excluded:
                continue
            if all_product_metadata:
                p_meta = all_product_metadata.get(pid, {})
                if not p_meta.get("is_active", True) or p_meta.get("stock", 1) <= 0:
                    continue
            valid_candidates.append(pid)

        if not valid_candidates:
            return []

        # 1. Candidate Scoring from Models
        # Collaborative Scores
        collab_raw = {}
        if user_id and user_id in self.collab_model.user_index_map:
            collab_raw = self.collab_model.predict_user_scores(user_id, valid_candidates)

        # Content-Based Scores
        content_raw = {}
        if user_interactions:
            content_raw = self.content_model.predict_user_scores(user_interactions, valid_candidates)
        elif user_preferences:
            # Cold-start profile synthesis from category preferences
            pref_interactions = []
            for pid in valid_candidates:
                p_meta = (all_product_metadata or {}).get(pid, {})
                cat_name = p_meta.get("category_name") or p_meta.get("category")
                if cat_name in user_preferences:
                    pref_interactions.append((pid, 2.0))
            if pref_interactions:
                content_raw = self.content_model.predict_user_scores(pref_interactions, valid_candidates)

        # Popularity Scores
        pop_raw = self.pop_model.predict_item_scores(valid_candidates)

        # 2. Score Normalization
        collab_norm = self._min_max_scale(collab_raw) if collab_raw else {pid: 0.0 for pid in valid_candidates}
        content_norm = self._min_max_scale(content_raw) if content_raw else {pid: 0.0 for pid in valid_candidates}
        pop_norm = self._min_max_scale(pop_raw) if pop_raw else {pid: 0.0 for pid in valid_candidates}

        # Dynamic weight adjustment for cold-start (when collab is empty)
        has_collab = bool(collab_raw)
        has_content = bool(content_raw)

        if not has_collab and has_content:
            w_collab, w_content, w_pop = 0.0, 0.70, 0.30
        elif not has_collab and not has_content:
            w_collab, w_content, w_pop = 0.0, 0.0, 1.0  # Pure Popularity Cold-Start
        else:
            w_collab, w_content, w_pop = self.w_collab, self.w_content, self.w_pop

        # 3. Hybrid Scoring
        hybrid_scores = {}
        score_breakdown = {}
        for pid in valid_candidates:
            c_score = collab_norm.get(pid, 0.0)
            t_score = content_norm.get(pid, 0.0)
            p_score = pop_norm.get(pid, 0.0)
            final_s = (w_collab * c_score) + (w_content * t_score) + (w_pop * p_score)

            hybrid_scores[pid] = final_s
            score_breakdown[pid] = {
                "collaborative_score": round(c_score, 4),
                "content_score": round(t_score, 4),
                "popularity_score": round(p_score, 4),
                "final_score": round(final_s, 4)
            }

        # 4. Maximal Marginal Relevance (MMR) Diversity Re-Ranking
        ranked_pids = self._apply_mmr(
            candidates=valid_candidates,
            scores=hybrid_scores,
            top_k=top_k,
            lambda_param=self.mmr_lambda
        )

        results = []
        for pid in ranked_pids:
            results.append({
                "product_id": pid,
                "score": hybrid_scores.get(pid, 0.0),
                "breakdown": score_breakdown.get(pid, {})
            })

        return results

    def _apply_mmr(
        self,
        candidates: List[str],
        scores: Dict[str, float],
        top_k: int,
        lambda_param: float
    ) -> List[str]:
        """
        Greedy Maximal Marginal Relevance selection:
        i* = argmax_{i in R \ S} [ lambda * Score(i) - (1 - lambda) * max_{j in S} Sim(i, j) ]
        """
        if not candidates:
            return []

        # Sort candidates initially by score
        pool = sorted(candidates, key=lambda x: scores.get(x, 0.0), reverse=True)[:50]
        selected: List[str] = []

        if not pool:
            return []

        # First item is purely highest scoring
        selected.append(pool[0])
        pool.remove(pool[0])

        sim_matrix = self.content_model.item_similarity_matrix
        idx_map = self.content_model.product_index_map

        while len(selected) < top_k and pool:
            best_item = None
            best_mmr_val = -float("inf")

            for candidate in pool:
                cand_score = scores.get(candidate, 0.0)

                # Find max similarity to already selected items
                max_sim = 0.0
                if sim_matrix is not None and candidate in idx_map:
                    c_idx = idx_map[candidate]
                    for s_item in selected:
                        if s_item in idx_map:
                            s_idx = idx_map[s_item]
                            sim = float(sim_matrix[c_idx, s_idx])
                            if sim > max_sim:
                                max_sim = sim

                mmr_val = lambda_param * cand_score - (1.0 - lambda_param) * max_sim
                if mmr_val > best_mmr_val:
                    best_mmr_val = mmr_val
                    best_item = candidate

            if best_item:
                selected.append(best_item)
                pool.remove(best_item)
            else:
                break

        return selected
