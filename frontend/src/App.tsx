import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { Navbar } from './components/Navbar';
import { CartDrawer } from './components/CartDrawer';
import { OnboardingModal } from './components/OnboardingModal';
import { HomePage } from './pages/HomePage';
import { ProductsPage } from './pages/ProductsPage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { Product } from './types';
import { Sparkles, Terminal, BookOpen, ExternalLink } from 'lucide-react';

export const AppContent: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'home' | 'products' | 'product_detail' | 'admin' | 'login' | 'register'>('home');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterCategoryId, setFilterCategoryId] = useState<number | undefined>(undefined);

  const handleNavigate = (page: string, param?: any) => {
    if (page === 'products' && param?.category_id !== undefined) {
      setFilterCategoryId(param.category_id);
      setSearchQuery('');
    } else {
      setFilterCategoryId(undefined);
    }
    setCurrentPage(page as any);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSearch = (q: string) => {
    setSearchQuery(q);
    setFilterCategoryId(undefined);
    setCurrentPage('products');
  };

  const handleSelectProduct = (product: Product) => {
    setSelectedProduct(product);
    setCurrentPage('product_detail');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0F19] text-slate-100 font-sans selection:bg-teal-500 selection:text-white">
      <Navbar
        currentPage={currentPage}
        onSearch={handleSearch}
        onNavigate={handleNavigate}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {currentPage === 'home' && (
          <HomePage
            onSelectProduct={handleSelectProduct}
            onNavigate={handleNavigate}
          />
        )}

        {currentPage === 'products' && (
          <ProductsPage
            initialCategoryId={filterCategoryId}
            initialSearchQuery={searchQuery}
            onSelectProduct={handleSelectProduct}
          />
        )}

        {currentPage === 'product_detail' && selectedProduct && (
          <ProductDetailPage
            product={selectedProduct}
            onBack={() => handleNavigate('home')}
            onSelectProduct={handleSelectProduct}
          />
        )}

        {currentPage === 'admin' && <AdminDashboardPage />}

        {currentPage === 'login' && (
          <LoginPage
            onSuccess={() => handleNavigate('home')}
            onNavigateRegister={() => handleNavigate('register')}
          />
        )}

        {currentPage === 'register' && (
          <RegisterPage
            onSuccess={() => handleNavigate('home')}
            onNavigateLogin={() => handleNavigate('login')}
          />
        )}
      </main>

      <CartDrawer />
      <OnboardingModal onCompleted={() => handleNavigate('home')} />

      {/* Modern Academic Presentation Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-10 mt-16 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold">
              AI
            </div>
            <div>
              <div className="text-white font-bold text-sm">RecommendAI Systems</div>
              <div className="text-[11px] text-slate-500">
                Final-Year ML/AI Capstone Project • Explainable Hybrid Recommendation Engine
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-slate-400">
            <span className="flex items-center gap-1.5 text-teal-400 font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>TF-IDF + Cosine</span>
            </span>
            <span className="flex items-center gap-1.5 text-indigo-400 font-medium">
              <Terminal className="w-3.5 h-3.5" />
              <span>Implicit ALS (Hu-Koren)</span>
            </span>
            <span className="flex items-center gap-1.5 text-amber-400 font-medium">
              <BookOpen className="w-3.5 h-3.5" />
              <span>FP-Growth Bundles</span>
            </span>
          </div>

          <div className="text-[11px] text-slate-500 text-center md:text-right">
            Offline Holdout Protocol: Leave-20%-Last • Negative Sampling 1:99
          </div>
        </div>
      </footer>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <AppContent />
      </CartProvider>
    </AuthProvider>
  );
}
