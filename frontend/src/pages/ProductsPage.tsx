import React, { useEffect, useState } from 'react';
import { Filter, SlidersHorizontal } from 'lucide-react';
import { Product, Category } from '../types';
import { productsApi } from '../services/api';
import { ProductCard } from '../components/ProductCard';

interface Props {
  initialCategoryId?: number;
  initialSearchQuery?: string;
  onSelectProduct: (product: Product) => void;
}

export const ProductsPage: React.FC<Props> = ({ initialCategoryId, initialSearchQuery, onSelectProduct }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCatId, setSelectedCatId] = useState<number | undefined>(initialCategoryId);
  const [sortBy, setSortBy] = useState<string>('popular');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    setSelectedCatId(initialCategoryId);
  }, [initialCategoryId]);

  useEffect(() => {
    const fetchCats = async () => {
      try {
        const cats = await productsApi.getCategories();
        setCategories(cats);
      } catch (e) {
        console.error('Failed to load categories', e);
      }
    };
    fetchCats();
  }, []);

  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      try {
        if (initialSearchQuery) {
          const res = await productsApi.search(initialSearchQuery);
          setProducts(res);
        } else {
          const res = await productsApi.getAll({
            category_id: selectedCatId,
            sort_by: sortBy,
            limit: 30,
          });
          setProducts(res.items);
        }
      } catch (e) {
        console.error('Failed to load products', e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProducts();
  }, [selectedCatId, sortBy, initialSearchQuery]);

  return (
    <div className="space-y-6 pb-16">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-card p-6 rounded-3xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {initialSearchQuery
              ? `Search Results for "${initialSearchQuery}"`
              : selectedCatId
              ? `${categories.find((c) => c.id === selectedCatId)?.name || 'Category'} Catalog`
              : 'Complete Product Catalog'}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Displaying {products.length} products curated with full feature vectors
          </p>
        </div>

        {/* Sort & Filter Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-teal-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <option value="popular">Most Popular</option>
              <option value="rating">Highest Rated</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="newest">Newest Additions</option>
            </select>
          </div>
        </div>
      </div>

      {/* Category Filter Pills */}
      {!initialSearchQuery && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <button
            onClick={() => setSelectedCatId(undefined)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
              selectedCatId === undefined
                ? 'bg-teal-500 text-slate-950 font-bold'
                : 'glass-card text-slate-300 hover:text-white'
            }`}
          >
            All Departments
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCatId(cat.id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                selectedCatId === cat.id
                  ? 'bg-teal-500 text-slate-950 font-bold'
                  : 'glass-card text-slate-300 hover:text-white'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}

      {/* Product Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="h-72 rounded-2xl bg-slate-900/60 animate-pulse border border-slate-800" />
          ))}
        </div>
      ) : products.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onSelect={onSelectProduct} />
          ))}
        </div>
      ) : (
        <div className="p-12 text-center glass-card rounded-2xl text-slate-400 text-sm">
          No products matched your criteria.
        </div>
      )}
    </div>
  );
};
