import React, { useState } from 'react';
import { ShoppingBag, Search, Sparkles, User as UserIcon, ShieldAlert, LogOut, Sliders } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { authApi } from '../services/api';

interface Props {
  onSearch: (query: string) => void;
  onNavigate: (page: string, param?: any) => void;
  currentPage: string;
}

export const Navbar: React.FC<Props> = ({ onSearch, onNavigate, currentPage }) => {
  const { user, logout, login, setShowOnboarding } = useAuth();
  const { totalItems, setIsCartOpen } = useCart();
  const [searchInput, setSearchInput] = useState('');
  const [isPersonaMenuOpen, setIsPersonaMenuOpen] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSearch(searchInput.trim());
    }
  };

  // Demo Persona Quick-Switch for Viva / Classroom Presentation
  const handleQuickSwitchPersona = async (email: string) => {
    setIsPersonaMenuOpen(false);
    try {
      const res = await authApi.login(email, 'password123');
      login(res.access_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
        role: res.role,
        preferred_categories: [],
        created_at: new Date().toISOString()
      });
      onNavigate('home');
    } catch (e) {
      console.error('Failed demo persona login', e);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div
          onClick={() => onNavigate('home')}
          className="flex items-center gap-2.5 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/25 group-hover:scale-105 transition">
            <Sparkles className="w-5 h-5 text-slate-950 fill-current" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-teal-400 via-cyan-300 to-white bg-clip-text text-transparent">
              Recommend<span className="text-teal-400">AI</span>
            </span>
            <span className="hidden sm:block text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
              Hybrid RecSys Engine
            </span>
          </div>
        </div>

        {/* Global Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md hidden md:block">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search products by specs, brand, tags (TF-IDF vector)..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition"
            />
          </div>
        </form>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {/* Demo Persona Switcher Pill */}
          <div className="relative">
            <button
              onClick={() => setIsPersonaMenuOpen(!isPersonaMenuOpen)}
              title="Quick-switch user persona for viva demonstration"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/60 transition"
            >
              <Sliders className="w-3.5 h-3.5 text-teal-400" />
              <span className="hidden lg:inline">Demo Persona</span>
            </button>

            {isPersonaMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl glass-panel p-2 shadow-2xl border border-slate-700 z-50">
                <div className="text-[11px] font-semibold text-slate-400 px-2 py-1 uppercase tracking-wider">
                  Select Persona (Viva Demo)
                </div>
                <button
                  onClick={() => handleQuickSwitchPersona('rahul.gamer@example.com')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-slate-800 flex flex-col transition"
                >
                  <span className="font-semibold text-teal-300">Rahul Sharma</span>
                  <span className="text-[10px] text-slate-400">Gamer Profile (Peripherals, OLEDs)</span>
                </button>
                <button
                  onClick={() => handleQuickSwitchPersona('sneha.audio@example.com')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-slate-800 flex flex-col transition"
                >
                  <span className="font-semibold text-indigo-300">Sneha Patel</span>
                  <span className="text-[10px] text-slate-400">Audiophile Profile (Studio, DACs)</span>
                </button>
                <button
                  onClick={() => handleQuickSwitchPersona('alex.dev@example.com')}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-slate-800 flex flex-col transition"
                >
                  <span className="font-semibold text-cyan-300">Alex Chen</span>
                  <span className="text-[10px] text-slate-400">Developer Profile (MacBook, Docks)</span>
                </button>
                <div className="border-t border-slate-800 my-1" />
                <button
                  onClick={() => {
                    setIsPersonaMenuOpen(false);
                    setShowOnboarding(true);
                  }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs text-amber-300 hover:bg-slate-800 font-medium transition"
                >
                  ✨ Test Cold-Start Onboarding
                </button>
              </div>
            )}
          </div>

          {/* Admin Dashboard shortcut */}
          {user?.role === 'ADMIN' ? (
            <button
              onClick={() => onNavigate('admin')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition border ${
                currentPage === 'admin'
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                  : 'bg-slate-800/80 text-rose-400 border-slate-700 hover:bg-slate-800'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Admin ModelOps</span>
            </button>
          ) : null}

          {/* User Profile / Auth State */}
          {user ? (
            <div className="flex items-center gap-2">
              <div
                onClick={() => onNavigate('profile')}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-teal-500/50 cursor-pointer transition"
              >
                <div className="w-6 h-6 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-xs font-bold">
                  {user.full_name[0]}
                </div>
                <span className="hidden sm:inline text-xs font-medium text-slate-200">
                  {user.full_name.split(' ')[0]}
                </span>
              </div>
              <button
                onClick={logout}
                title="Logout"
                className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => onNavigate('login')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-semibold transition shadow-md shadow-teal-500/20"
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
          )}

          {/* Shopping Cart Button */}
          <button
            onClick={() => setIsCartOpen(true)}
            className="relative p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-teal-500/50 text-slate-300 hover:text-white transition active:scale-95"
          >
            <ShoppingBag className="w-4 h-4" />
            {totalItems > 0 && (
              <span className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-teal-500 text-slate-950 text-[10px] font-extrabold flex items-center justify-center shadow-lg">
                {totalItems}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
