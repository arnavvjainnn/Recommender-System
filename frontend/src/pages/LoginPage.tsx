import React, { useState } from 'react';
import { User, Lock, ArrowRight, Sparkles } from 'lucide-react';
import { authApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface Props {
  onSuccess: () => void;
  onNavigateRegister: () => void;
}

export const LoginPage: React.FC<Props> = ({ onSuccess, onNavigateRegister }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const res = await authApi.login(email, password);
      login(res.access_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
        role: res.role,
        preferred_categories: [],
        created_at: new Date().toISOString(),
      });
      onSuccess();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4">
      <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6 shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-teal-500/10 text-teal-400">
            <User className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sign In to RecommendAI</h1>
          <p className="text-xs text-slate-400">
            Experience your personalized recommendation matrix and browsing history
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. rahul.gamer@example.com"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-300">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition active:scale-95 shadow-lg shadow-teal-500/25"
          >
            <span>{isLoading ? 'Signing In...' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Viva Quick Login Buttons */}
        <div className="border-t border-slate-800 pt-4 space-y-2">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-center">
            Demo Persona Quick-Fill
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => handleQuickFill('rahul.gamer@example.com', 'password123')}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-teal-300 hover:bg-slate-800 text-left font-medium transition"
            >
              🎮 Rahul (Gamer)
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('sneha.audio@example.com', 'password123')}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-indigo-300 hover:bg-slate-800 text-left font-medium transition"
            >
              🎧 Sneha (Audio)
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('alex.dev@example.com', 'password123')}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-cyan-300 hover:bg-slate-800 text-left font-medium transition"
            >
              💻 Alex (Developer)
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('admin@recommendai.com', 'adminpassword123')}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-rose-300 hover:bg-slate-800 text-left font-medium transition"
            >
              🛡️ Admin Ops
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-slate-400">
          Don't have an account?{' '}
          <button
            onClick={onNavigateRegister}
            className="text-teal-400 hover:text-teal-300 font-semibold"
          >
            Sign up now
          </button>
        </div>
      </div>
    </div>
  );
};
