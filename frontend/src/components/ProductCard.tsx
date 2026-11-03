import React from 'react';
import { Star, ShoppingCart, Heart } from 'lucide-react';
import { Product, RecommendationExplanation } from '../types';
import { ExplanationBadge } from './ExplanationBadge';
import { useCart } from '../context/CartContext';
import { interactionsApi } from '../services/api';

interface Props {
  product: Product;
  explanation?: RecommendationExplanation;
  onSelect?: (product: Product) => void;
}

export const ProductCard: React.FC<Props> = ({ product, explanation, onSelect }) => {
  const { addToCart } = useCart();

  const handleCardClick = () => {
    interactionsApi.log(product.id, 'CLICK');
    if (onSelect) {
      onSelect(product);
    }
  };

  const handleAddToCart = (e: React.MouseEvent) => {
    e.stopPropagation();
    addToCart(product);
  };

  const handleLike = (e: React.MouseEvent) => {
    e.stopPropagation();
    interactionsApi.log(product.id, 'LIKE');
  };

  const discountedPrice = product.discount_percent > 0
    ? product.price * (1 - product.discount_percent / 100)
    : product.price;

  return (
    <div
      onClick={handleCardClick}
      className="group relative flex flex-col rounded-2xl glass-card overflow-hidden hover:border-teal-500/50 hover:shadow-2xl hover:shadow-teal-950/20 transition-all duration-300 cursor-pointer"
    >
      {/* Top Floating Pill / Explanation Badge */}
      <div className="absolute top-3 left-3 right-3 flex justify-between items-start z-10">
        {explanation ? (
          <ExplanationBadge explanation={explanation} />
        ) : product.discount_percent > 0 ? (
          <span className="bg-rose-500/90 text-white text-[11px] font-semibold px-2 py-0.5 rounded-full shadow-sm">
            {product.discount_percent}% OFF
          </span>
        ) : <div />}

        <button
          onClick={handleLike}
          aria-label="Wishlist"
          className="p-1.5 rounded-full bg-slate-900/60 backdrop-blur-md text-slate-300 hover:text-rose-400 hover:bg-slate-900/90 transition"
        >
          <Heart className="w-4 h-4" />
        </button>
      </div>

      {/* Product Image */}
      <div className="relative w-full h-52 bg-slate-900/50 overflow-hidden flex items-center justify-center">
        <img
          src={product.image_url}
          alt={product.title}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-60 group-hover:opacity-40 transition-opacity" />
      </div>

      {/* Product Content Details */}
      <div className="flex flex-col flex-1 p-4 justify-between gap-3">
        <div>
          <div className="flex items-center justify-between text-xs text-teal-400 font-medium mb-1">
            <span>{product.brand}</span>
            <div className="flex items-center gap-1 text-amber-400">
              <Star className="w-3.5 h-3.5 fill-current" />
              <span>{product.rating.toFixed(1)}</span>
              <span className="text-slate-500">({product.rating_count})</span>
            </div>
          </div>

          <h3 className="font-semibold text-sm text-slate-100 line-clamp-2 leading-snug group-hover:text-teal-300 transition-colors">
            {product.title}
          </h3>

          {/* Explanation rationale footer if present */}
          {explanation?.reason_text && (
            <p className="mt-2 text-[11px] text-slate-400 line-clamp-1 italic">
              "{explanation.reason_text}"
            </p>
          )}
        </div>

        {/* Pricing & Add to Cart Action */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <div>
            <span className="text-lg font-bold text-white tracking-tight">
              ${discountedPrice.toFixed(2)}
            </span>
            {product.discount_percent > 0 && (
              <span className="ml-2 text-xs text-slate-500 line-through">
                ${product.price.toFixed(2)}
              </span>
            )}
          </div>

          <button
            onClick={handleAddToCart}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs transition active:scale-95 shadow-md shadow-teal-500/20"
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            <span>Add</span>
          </button>
        </div>
      </div>
    </div>
  );
};
