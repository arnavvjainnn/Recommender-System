# RecommendAI — College Viva Voce & Academic Defense Guide

This guide prepares you for common, challenging questions asked by professors, project guides, and external examiners during final-year project evaluations and viva voce examinations.

---

## 1. Core Machine Learning & Recommendation Systems

### Q1: What makes RecommendAI a real ML recommendation system rather than simple database filtering?
**Answer:**
A naive filtering system uses hardcoded boolean rules (e.g. `WHERE category = 'gaming'`). In contrast, RecommendAI uses mathematical model spaces:
1. **Content-Based:** Constructs continuous TF-IDF vector spaces $\mathbf{v}_i \in \mathbb{R}^{5000}$ over composite metadata and projects user preference vectors $\mathbf{p}_u = \sum r_{ui} \mathbf{v}_i$ to calculate cosine similarity angles.
2. **Collaborative Filtering:** Uses **Implicit Alternating Least Squares (iALS)** to decompose the sparse user-item interaction matrix into $f$-dimensional latent factor spaces ($\mathbf{x}_u, \mathbf{y}_i \in \mathbb{R}^{32}$) optimizing confidence-weighted preference loss.
3. **Hybrid Re-ranking:** Normalizes separate model probability distributions and balances relevance against diversity using **Maximal Marginal Relevance (MMR)**.

---

### Q2: Why did you choose Implicit ALS (Hu, Koren, Volinsky) instead of classic SVD or Surpr!se SVD?
**Answer:**
Classic SVD (like the Netflix Prize SVD) requires **explicit feedback** (1 to 5 star ratings) and treats missing entries as unknown or zeros. In modern e-commerce:
- Explicit ratings constitute less than $1\%$ of user actions.
- Clicks, views, cart additions, and purchases are **implicit feedback**. There are no explicit negative ratings (a user simply did not click an item).
- **iALS** solves this by defining preference $p_{ui} \in \{0, 1\}$ and confidence $c_{ui} = 1 + \alpha r_{ui}$. Unobserved entries are treated as zero preference with low baseline confidence ($c_{ui} = 1$), while observed interactions increase confidence proportionally to user engagement intensity.

---

### Q3: How do you address the Cold-Start problem for both new users and new products?
**Answer:**
We decouple cold-start into two distinct failure modes:
1. **New User Cold-Start:** When a user registers with zero historical interactions, the user row in the collaborative matrix is empty. We solve this via:
   - **Interest Onboarding Modal:** Asking the user to select 2 or more category interests upon registration.
   - **Synthetic Profile Projection:** Constructing a synthetic content-based vector directly from the chosen categories.
   - **Time-Decayed Global Popularity:** Blending trending velocity products with the user's category preferences.
2. **New Product Cold-Start:** When a merchant uploads a new product with zero clicks or purchases, the item column in the collaborative matrix is empty. We solve this via **Pure Content-Based Projection**: the item's TF-IDF vector is computed immediately from its title, brand, description, and tags, enabling it to appear in "Similar Products" and search without needing historical purchases.

---

### Q4: Why did you use Precision@K, Recall@K, and NDCG@K instead of Mean Squared Error (MSE) / RMSE?
**Answer:**
- **RMSE** measures the difference between actual and predicted numeric ratings across the entire catalog. In e-commerce, the user never sees 99.9% of the catalog, so rating accuracy on uninteracted items is irrelevant.
- E-commerce recommendations are fundamentally a **Top-K Ranking Problem**.
- **Precision@K** and **Recall@K** evaluate whether relevant items appear in the visible top 5 or 10 slots.
- **NDCG@K (Normalized Discounted Cumulative Gain)** accounts for position bias using a logarithmic discount ($\frac{1}{\log_2(\text{rank}+1)}$), rewarding models that place the most relevant products at rank 1 rather than rank 10.

---

### Q5: How did you evaluate the model without data leakage?
**Answer:**
We strictly avoided random cross-validation because user browsing behavior is sequential and time-dependent. Instead:
1. **Temporal Train/Test Split:** We partitioned interactions chronologically per user. The first $80\%$ of historical events were placed in the training set, and the subsequent $20\%$ were placed in the holdout test set.
2. **1:99 Negative Sampling Protocol:** For each ground-truth item in the test set, we randomly sampled 99 uninteracted items from the catalog. The model ranked the 100-item pool, standardizing HitRate@10 and NDCG@10 metrics.

---

### Q6: What is Maximal Marginal Relevance (MMR) and why is it needed in e-commerce?
**Answer:**
Without MMR, top recommendations often suffer from severe redundancy (e.g. recommending 8 slightly different mechanical keyboards from the same brand). MMR balances relevance and novelty greedily:
$$\text{MMR} = \arg\max_{i \in R \setminus S} \left[ \lambda \cdot S_{final}(u, i) - (1 - \lambda) \cdot \max_{j \in S} \text{Sim}_{content}(i, j) \right]$$
When $\lambda = 0.75$, the system selects products that have high hybrid predicted scores while penalizing items that are acoustically or textually redundant with items already selected in the top list.

---

### Q7: How does your association rule mining differ from the collaborative filtering model?
**Answer:**
- **Collaborative Filtering** captures general user affinity across sessions and time (e.g., "users who like mechanical keyboards tend to also like gaming monitors").
- **Association Rule Mining (FP-Growth)** operates at the transactional basket level to detect complementary add-ons (e.g., "Shoppers who purchase a DSLR Camera also buy an SD Card and Camera Bag"). We measure rules using:
  - **Support:** $P(A \cap B)$
  - **Confidence:** $P(B|A)$
  - **Lift:** $\frac{P(A \cap B)}{P(A)P(B)}$ (Lift $> 1$ indicates strong positive association beyond random co-occurrence).

---

## 2. Architecture, Performance & Scalability

### Q8: How does your system guarantee sub-150ms recommendation response times?
**Answer:**
We separate **offline training** from **online serving**:
1. All expensive matrix factorizations, TF-IDF vector matrices, and association rules are precomputed offline and serialized into in-memory caches.
2. Online recommendation serving performs only vector dot products ($\mathbf{x}_u^T \mathbf{y}_i$ or $\mathbf{p}_u \cdot \mathbf{v}_i$) and hash map lookups.
3. Database queries for stock verification and excluded purchases use composite indexes on `(user_id, created_at DESC)` and `(category_id, is_active)`.

---

### Q9: Why FastAPI over Django or Flask?
**Answer:**
FastAPI is built on Starlette and Uvicorn, utilizing Python's `asyncio` event loop. This enables high concurrency for I/O-bound telemetry logging while maintaining zero-copy native compatibility with Python numerical arrays (`numpy`, `scipy`). Additionally, FastAPI provides automatic OpenAPI / Swagger interactive documentation and Pydantic v2 data contract validation.

---

### Q10: How are recommendation explanations generated?
**Answer:**
Explanations are derived directly from the normalized component scores:
- If $S_{content} > 0.35$ and dominates, the reason is attributed to the user's recently browsed items in that category.
- If $S_{collab} > 0.35$ and dominates, the reason explains community peer similarity.
- If derived from an order basket, the reason attributes the complementary add-on with the Lift metric.
This ensures zero hallucinated explanations.
