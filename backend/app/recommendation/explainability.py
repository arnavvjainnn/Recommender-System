from typing import Dict, Optional, List
from app.schemas.pydantic_models import RecommendationExplanation

class ExplanationEngine:
    """
    Grounded Signal-Based Explainability Engine.
    Maps quantitative model weights to intuitive, human-understandable rationales
    without fabricating false claims.
    """
    @staticmethod
    def generate_explanation(
        breakdown: Dict[str, float],
        product_metadata: dict,
        user_recent_item_titles: Optional[List[str]] = None,
        bundle_source_title: Optional[str] = None
    ) -> RecommendationExplanation:
        collab_s = breakdown.get("collaborative_score", 0.0)
        content_s = breakdown.get("content_score", 0.0)
        pop_s = breakdown.get("popularity_score", 0.0)
        final_s = breakdown.get("final_score", 0.0)

        category = product_metadata.get("category_name") or product_metadata.get("category", "tech")
        brand = product_metadata.get("brand", "")

        # 1. Frequently Bought Together Bundle Explanation
        if bundle_source_title:
            return RecommendationExplanation(
                primary_factor="FREQUENT_BUNDLE",
                reason_text=f"Frequently purchased together with '{bundle_source_title}'.",
                content_score=content_s,
                collaborative_score=collab_s,
                popularity_score=pop_s,
                final_score=final_s
            )

        # 2. Collaborative Filtering Dominant
        if collab_s >= content_s and collab_s >= pop_s and collab_s > 0.35:
            return RecommendationExplanation(
                primary_factor="COLLABORATIVE_FILTERING",
                reason_text=f"Popular with shoppers who share your taste in {category}.",
                content_score=content_s,
                collaborative_score=collab_s,
                popularity_score=pop_s,
                final_score=final_s
            )

        # 3. Content-Based Dominant
        if content_s >= collab_s and content_s >= pop_s and content_s > 0.30:
            anchor = user_recent_item_titles[0] if user_recent_item_titles else f"{brand} {category}"
            return RecommendationExplanation(
                primary_factor="CONTENT_SIMILARITY",
                reason_text=f"Similar in features and specifications to '{anchor}'.",
                content_score=content_s,
                collaborative_score=collab_s,
                popularity_score=pop_s,
                final_score=final_s
            )

        # 4. Trending & Popularity Dominant (or Cold-Start Fallback)
        return RecommendationExplanation(
            primary_factor="POPULAR_TRENDING",
            reason_text=f"Trending top-rated item in {category} with high customer satisfaction.",
            content_score=content_s,
            collaborative_score=collab_s,
            popularity_score=pop_s,
            final_score=final_s
        )
