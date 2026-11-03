import React, { useEffect, useState } from 'react';
import { Star, ShoppingCart, Heart, ShieldCheck, Truck, ArrowLeft, PackagePlus, Sparkles, Send } from 'lucide-react';
import { Product, RecommendedProduct } from '../types';
import { recommendationsApi, interactionsApi, productsApi } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

interface Props {
  product: Product;
  onBack: () => void;
  onSelectProduct: (product: Product) => void;
}

export const ProductDetailPage: React.FC<Props> = ({ product, onBack, onSelectProduct }) => {
  const { addToCart } = useCart();
  const { user } = useAuth();
  const [similarProducts, setSimilarProducts] = useState<RecommendedProduct[]>([]);
  const [bundleProducts, setBundleProducts] = useState<RecommendedProduct[]>([]);
  const [userRating, setUserRating] = useState<number>(5);
  const [reviewText, setReviewText] = useState<string>('');
  const [ratingSubmitted, setRatingSubmitted] = useState<boolean>(false);
  const [activeProduct, setActiveProduct] = useState<Product>(product);

  useEffect(() => {
    setActiveProduct(product);
    // Log VIEW event
    interactionsApi.log(product.id, 'VIEW');

    // Fetch Content-based Similar Products & FP-Growth Frequently Bought Together
    const fetchRecs = async () => {
      try {
        const [sim, bundles] = await Promise.all([
          recommendationsApi.getSimilar(product.id, 4),
          recommendationsApi.getFrequentlyBought(product.id, 3),
        ]);
        setSimilarProducts(sim);
        setBundleProducts(bundles);
      } catch (e) {
        console.error('Failed to fetch item recs', e);
      }
    };

    fetchRecs();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [product.id]);

  const handleRatingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await interactionsApi.rate(activeProduct.id, userRating, reviewText);
      setRatingSubmitted(true);
      // Refresh product data
      const updated = await productsApi.getById(activeProduct.id);
      setActiveProduct(updated);
    } catch (e) {
      console.error('Failed to submit rating', e);
    }
  };

  const discountedPrice = activeProduct.discount_percent > 0
    ? activeProduct.price * (1 - activeProduct.discount_percent / 100)
    : activeProduct.price;

  return (
    <div className="space-y-12 pb-16">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white hover:border-slate-700 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Storefront</span>
      </button>

      {/* Product Hero Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Product Image */}
        <div className="rounded-3xl glass-card overflow-hidden p-4 border border-slate-800 flex items-center justify-center bg-slate-950/40">
          <img
            src={activeProduct.image_url}
            alt={activeProduct.title}
            className="w-full h-96 sm:h-[450px] object-cover rounded-2xl"
          />
        </div>

        {/* Product Meta & Actions */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-teal-400 mb-1">
              <span>{activeProduct.brand}</span>
              <span>•</span>
              <span className="text-slate-400">{activeProduct.category_name}</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {activeProduct.title}
            </h1>

            {/* Ratings Bar */}
            <div className="flex items-center gap-3 mt-2">
              <div className="flex items-center gap-1 text-amber-400">
                <Star className="w-4 h-4 fill-current" />
                <span className="text-sm font-bold">{activeProduct.rating.toFixed(1)}</span>
              </div>
              <span className="text-xs text-slate-400">
                Based on {activeProduct.rating_count} verified reviews
              </span>
              <span className="text-slate-600">|</span>
              <span className="text-xs text-emerald-400 font-medium">In Stock ({activeProduct.stock} units)</span>
            </div>
          </div>

          {/* Pricing */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-3xl font-extrabold text-white">
                ${discountedPrice.toFixed(2)}
              </span>
              {activeProduct.discount_percent > 0 && (
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-sm text-slate-500 line-through">
                    ${activeProduct.price.toFixed(2)}
                  </span>
                  <span className="text-xs font-bold text-rose-400">
                    Save {activeProduct.discount_percent}%
                  </span>
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => addToCart(activeProduct)}
                className="px-5 py-3 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs sm:text-sm flex items-center gap-2 transition active:scale-95 shadow-lg shadow-teal-500/25"
              >
                <ShoppingCart className="w-4 h-4" />
                <span>Add to Cart</span>
              </button>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Product Overview & Specifications
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              {activeProduct.description}
            </p>
          </div>

          {/* Tags */}
          {activeProduct.tags && activeProduct.tags.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-bold text-slate-400">Catalog Features (TF-IDF Tokens):</h4>
              <div className="flex flex-wrap gap-1.5">
                {activeProduct.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-teal-300"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Trust Guarantees */}
          <div className="grid grid-cols-2 gap-3 pt-2 text-xs text-slate-400 border-t border-slate-800">
            <div className="flex items-center gap-2">
              <Truck className="w-4 h-4 text-teal-400" />
              <span>Simulated Campus Delivery</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-400" />
              <span>Full ML Telemetry Verified</span>
            </div>
          </div>
        </div>
      </div>

      {/* Star Rating Submission Box */}
      <section className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Star className="w-4 h-4 text-amber-400 fill-current" />
          <span>Rate & Review This Product (Explicit Interaction Telemetry)</span>
        </h3>

        {ratingSubmitted ? (
          <div className="p-4 rounded-xl bg-teal-950/40 border border-teal-500/30 text-teal-300 text-xs">
            Thank you! Your rating has been logged. The collaborative filtering matrix and Bayesian averages will incorporate your score.
          </div>
        ) : (
          <form onSubmit={handleRatingSubmit} className="space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400">Your Rating:</span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setUserRating(star)}
                    className="p-1 text-slate-600 hover:text-amber-400 transition"
                  >
                    <Star
                      className={`w-5 h-5 ${
                        star <= userRating ? 'text-amber-400 fill-current' : ''
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Optional review note (e.g. 'Crisp sound, great switches')..."
                value={reviewText}
                onChange={(e) => setReviewText(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white flex items-center gap-1.5 transition"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit Rating</span>
              </button>
            </div>
          </form>
        )}
      </section>

      {/* Frequently Bought Together Bundle (FP-Growth Lift) */}
      {bundleProducts.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <PackagePlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Frequently Bought Together
              </h2>
              <p className="text-xs text-slate-400">
                Association rule bundles mined using FP-Growth basket co-occurrence with high Lift metrics
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {bundleProducts.map((rec) => (
              <ProductCard
                key={rec.product.id}
                product={rec.product}
                explanation={rec.explanation}
                onSelect={onSelectProduct}
              />
            ))}
          </div>
        </section>
      )}

      {/* Similar Products Section (Content-Based TF-IDF) */}
      {similarProducts.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                Similar Products
              </h2>
              <p className="text-xs text-slate-400">
                Calculated via TF-IDF vectorization and Cosine Similarity over metadata attributes
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {similarProducts.map((rec) => (
              <ProductCard
                key={rec.product.id}
                product={rec.product}
                explanation={rec.explanation}
                onSelect={onSelectProduct}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
