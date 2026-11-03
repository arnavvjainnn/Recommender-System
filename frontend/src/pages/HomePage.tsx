import React, { useEffect, useState } from 'react';
import { Sparkles, TrendingUp, Award, Layers, ArrowRight, Zap } from 'lucide-react';
import { RecommendedProduct, Product } from '../types';
import { recommendationsApi, productsApi } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';

interface Props {
  onSelectProduct: (product: Product) => void;
  onNavigate: (page: string, param?: any) => void;
}

export const HomePage: React.FC<Props> = ({ onSelectProduct, onNavigate }) => {
  const { user, setShowOnboarding } = useAuth();
  const [personalizedRecs, setPersonalizedRecs] = useState<RecommendedProduct[]>([]);
  const [trendingRecs, setTrendingRecs] = useState<RecommendedProduct[]>([]);
  const [popularRecs, setPopularRecs] = useState<RecommendedProduct[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    try {
      const [personalized, trending, popular, cats] = await Promise.all([
        recommendationsApi.getPersonalized(8),
        recommendationsApi.getTrending(4),
        recommendationsApi.getPopular(4),
        productsApi.getCategories(),
      ]);
      setPersonalizedRecs(personalized);
      setTrendingRecs(trending);
      setPopularRecs(popular);
      setCategories(cats);
    } catch (e) {
      console.error('Error fetching home recommendations', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [user]);

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Banner */}
      <section className="relative overflow-hidden rounded-3xl glass-panel border border-teal-500/20 p-8 sm:p-12 shadow-2xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-16 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-semibold">
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>Multi-Model Hybrid Recommendation Architecture</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
            Curated For You by <br />
            <span className="bg-gradient-to-r from-teal-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
              Real Machine Learning.
            </span>
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
            Experience real-time candidate retrieval combining <strong className="text-teal-300">TF-IDF Content Similarity</strong>,{' '}
            <strong className="text-indigo-300">Implicit ALS Matrix Factorization</strong>, and{' '}
            <strong className="text-cyan-300">MMR Diversity Re-ranking</strong> with explainable match signals.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => onNavigate('products')}
              className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs sm:text-sm flex items-center gap-2 transition active:scale-95 shadow-lg shadow-teal-500/20"
            >
              <span>Explore Entire Catalog</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => setShowOnboarding(true)}
              className="px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold text-xs sm:text-sm transition flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-teal-400" />
              <span>Simulate Cold-Start Setup</span>
            </button>
          </div>
        </div>
      </section>

      {/* Category Pills Bar */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
            Browse by Department
          </h2>
          <button
            onClick={() => onNavigate('products')}
            className="text-xs text-teal-400 hover:text-teal-300 font-semibold flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        <div className="flex items-center gap-2.5 overflow-x-auto pb-2 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => onNavigate('products', { category_id: cat.id })}
              className="flex-shrink-0 px-4 py-2 rounded-xl glass-card hover:border-teal-500/50 text-xs font-semibold text-slate-200 hover:text-white transition shadow-sm"
            >
              {cat.name}
            </button>
          ))}
        </div>
      </section>

      {/* Section 1: Personalized Recommendations */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                {user ? `Personalized For ${user.full_name}` : 'Recommended For Your Session'}
              </h2>
              <p className="text-xs text-slate-400">
                Dynamically scored using Hybrid iALS + TF-IDF profile match and MMR diversity
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-72 rounded-2xl bg-slate-900/60 animate-pulse border border-slate-800" />
            ))}
          </div>
        ) : personalizedRecs.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {personalizedRecs.map((rec) => (
              <ProductCard
                key={rec.product.id}
                product={rec.product}
                explanation={rec.explanation}
                onSelect={onSelectProduct}
              />
            ))}
          </div>
        ) : (
          <div className="p-8 text-center glass-card rounded-2xl text-slate-400 text-sm">
            No recommendations generated yet. Browse products or try the cold-start selector!
          </div>
        )}
      </section>

      {/* Section 2: Trending Momentum */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
              Trending Momentum
            </h2>
            <p className="text-xs text-slate-400">
              Calculated via exponential time-decay kernel with 7-day velocity boost
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {trendingRecs.map((rec) => (
            <ProductCard
              key={rec.product.id}
              product={rec.product}
              explanation={rec.explanation}
              onSelect={onSelectProduct}
            />
          ))}
        </div>
      </section>

      {/* Section 3: Community Favorites (Popularity Baseline) */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
              Community Favorites
            </h2>
            <p className="text-xs text-slate-400">
              Global baseline ranked by Bayesian smoothed rating and historical orders
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {popularRecs.map((rec) => (
            <ProductCard
              key={rec.product.id}
              product={rec.product}
              explanation={rec.explanation}
              onSelect={onSelectProduct}
            />
          ))}
        </div>
      </section>
    </div>
  );
};
