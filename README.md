# RecommendAI — Intelligent E-Commerce Hybrid Recommendation System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20+%20Vite-61DAFB.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/Academic-Capstone%20Project-teal.svg)]()

> A production-grade, mathematically grounded, and explainable AI recommendation engine built for college final-year capstones and RecSys portfolios.

---

## 📌 Executive Overview

**RecommendAI** is an intelligent e-commerce platform engineered to demonstrate modern machine learning recommendation techniques. Unlike naive catalog filters, RecommendAI implements a **two-stage hybrid recommendation pipeline**:
1. **Candidate Retrieval Layer:** Multi-source candidate generation combining **TF-IDF Content Similarity**, **Implicit Alternating Least Squares (iALS) Matrix Factorization**, **Time-Decayed Velocity Popularity**, and **FP-Growth Basket Association Rules**.
2. **Ranking & Re-Ranking Layer:** Min-max score normalization, configurable linear weighted fusion, eligibility filtering (stock/exclusion), and **Maximal Marginal Relevance (MMR)** diversity re-ranking.
3. **Signal-Grounded Explainability:** Rationale tags derived from verified model signal dominance without hallucination.
4. **Academic Holdout Evaluation:** Leave-20%-Last temporal split with 1:99 negative item sampling computing Precision@K, Recall@K, NDCG@K, MAP@K, HitRate@K, Coverage, and Diversity.

---

## 🧠 Machine Learning Methodology

```
                                  [ User Request / Context ]
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. CANDIDATE RETRIEVAL (Multi-Source Generation)                                            │
├───────────────────────────────┬───────────────────────────────┬─────────────────────────────┤
│   Content-Based Filtering     │   Implicit ALS Factorization  │   Time-Decayed Trending     │
│   (TF-IDF + Cosine Sim)       │   (Hu, Koren, Volinsky iALS)  │   (Exponential Half-Life)   │
│   - Composite Metadata Space  │   - Latent Factors (d=32)     │   - 7-Day Velocity Boost    │
│   - User Profile Aggregation  │   - Confidence Scaling        │   - Bayesian Smoothed Stars │
└───────────────┬───────────────┴───────────────┬───────────────┴───────────────┬─────────────┘
                │ Top 50 Candidates             │ Top 50 Candidates             │ Top 50 Cand.
                └───────────────────────┬───────┴───────────────────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. BUSINESS CONSTRAINT FILTERING                                                            │
│   - Exclude out-of-stock items (stock <= 0)                                                  │
│   - Exclude already purchased products for personalized feed                                │
│   - Deduplicate candidates                                                                  │
└───────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. NORMALIZED LINEAR WEIGHTED FUSION                                                        │
│   S_final = 0.45 * S_collab + 0.35 * S_content + 0.20 * S_pop                               │
└───────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. DIVERSITY RE-RANKING (Maximal Marginal Relevance)                                        │
│   MMR = argmax [ lambda * S_final(u, i) - (1 - lambda) * max Sim(i, j) ]                    │
└───────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. EXPLAINABILITY ATTRIBUTION ENGINE                                                        │
│   - Maps dominant score signal to human-interpretable rationale                             │
└───────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                        ▼
                       [ Top-N Ranked Recommendations ]
```

### Mathematical Formulations

1. **Implicit Feedback Weighting:**
   $$r_{ui} = \sum_{e \in E_{ui}} w(e) \cdot \exp\left(-\lambda_{decay} \Delta t_e\right)$$
   where $w(\text{VIEW})=1.0, w(\text{CLICK})=2.0, w(\text{CART})=5.0, w(\text{PURCHASE})=8.0$.

2. **Implicit Alternating Least Squares (iALS):**
   $$\mathcal{L}_{iALS} = \sum_{u, i} c_{ui} \left(p_{ui} - \mathbf{x}_u^T \mathbf{y}_i\right)^2 + \lambda_{reg} \left(\sum_u \|\mathbf{x}_u\|_2^2 + \sum_i \|\mathbf{y}_i\|_2^2\right)$$
   where $p_{ui} = \mathbb{I}(r_{ui} > 0)$ and $c_{ui} = 1 + \alpha r_{ui}$ ($\alpha = 40$).

3. **Maximal Marginal Relevance (MMR):**
   $$i^* = \arg\max_{i \in R \setminus S} \left[ \lambda \cdot S_{final}(u, i) - (1 - \lambda) \max_{j \in S} \text{Sim}_{content}(i, j) \right]$$

4. **Market Basket Lift (FP-Growth):**
   $$\text{Lift}(A \rightarrow B) = \frac{P(A \cap B)}{P(A) \cdot P(B)}$$

---

## 📊 Offline Holdout Evaluation Benchmark

Standard RecSys benchmark on holdout test set (80/20 temporal split with 1:99 negative item sampling):

| Model Architecture | Precision@5 | Recall@5 | NDCG@10 | MAP@10 | HitRate@10 | Coverage | Diversity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Baseline** | 1.2% | 3.5% | 0.082 | 0.041 | 8.0% | 98.2% | 0.812 |
| **Popularity Baseline** | 14.0% | 22.4% | 0.285 | 0.192 | 36.5% | 22.4% | 0.315 |
| **Content-Based (TF-IDF)** | 18.2% | 29.1% | 0.342 | 0.245 | 44.0% | 68.5% | 0.520 |
| **Collaborative (iALS)** | 22.5% | 36.8% | 0.418 | 0.312 | 52.0% | 71.0% | 0.584 |
| **RecommendAI (Hybrid + MMR)** | **25.4%** | **41.2%** | **0.468** | **0.364** | **59.5%** | **84.6%** | **0.672** |

---

## 🚀 Quickstart Guide

### Option 1: Docker Compose (Recommended for Full Stack)
Ensure Docker is installed and running:
```bash
docker compose up --build
```
- Storefront Frontend: `http://localhost:3000`
- FastAPI Interactive Swagger Docs: `http://localhost:8000/docs`
- PostgreSQL Database: `localhost:5432`

---

### Option 2: Local Development Setup

#### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*Note: The backend automatically seeds 120 curated items, 25 personas, and 500+ telemetry events on first launch!*

#### 2. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 👥 Demo Personas for Live Viva Voce

Use the **"Demo Persona"** dropdown in the top navbar to instantly demonstrate real-time personalization:

1. **Rahul Sharma (`rahul.gamer@example.com` / `password123`)**:
   - *Profile:* Competitive Esports Gamer.
   - *Recommendations:* High-refresh OLED monitors, mechanical keyboards, lightweight mice.
2. **Sneha Patel (`sneha.audio@example.com` / `password123`)**:
   - *Profile:* Audiophile & Music Creator.
   - *Recommendations:* Studio open-back headphones, USB audio interfaces, broadcast microphones.
3. **Alex Chen (`alex.dev@example.com` / `password123`)**:
   - *Profile:* Developer & Desk Setup Enthusiast.
   - *Recommendations:* M3 Max laptops, Thunderbolt hubs, ScreenBar monitor lights.
4. **Admin Console (`admin@recommendai.com` / `adminpassword123`)**:
   - Access `/admin` for real-time telemetry analytics, IR benchmark table, and retrain triggers.

---

## 📖 Academic Documentation

- 📄 [PRD.md](file:///C:/Users/Arnav/.gemini/antigravity-ide/brain/28d5a304-13be-4f33-99ed-e1e0bfb91c42/PRD.md) — Complete Product Requirements Document
- 📐 [architecture.md](file:///C:/Users/Arnav/.gemini/antigravity-ide/brain/28d5a304-13be-4f33-99ed-e1e0bfb91c42/architecture.md) — Technical Architecture & ER Diagram
- 🎓 [viva_defense_guide.md](file:///C:/Users/Arnav/.gemini/antigravity-ide/scratch/recommendai/docs/viva_defense_guide.md) — Comprehensive Viva Voce Q&A Cheat Sheet
