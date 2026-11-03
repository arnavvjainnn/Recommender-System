import React, { useEffect, useState } from 'react';
import { ShieldCheck, Activity, Users, ShoppingBag, Eye, RefreshCw, BarChart3, CheckCircle2, Award } from 'lucide-react';
import { AnalyticsOverview, ModelMetrics } from '../types';
import { adminApi } from '../services/api';

export const AdminDashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);
  const [retrainSuccess, setRetrainSuccess] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [ov, met] = await Promise.all([
        adminApi.getOverview(),
        adminApi.getModelMetrics(),
      ]);
      setOverview(ov);
      setMetrics(met);
    } catch (e) {
      console.error('Failed to load admin telemetry', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRetrain = async () => {
    setIsRetraining(true);
    setRetrainSuccess(false);
    try {
      await adminApi.retrain({ epochs: 15, factors: 32 });
      setRetrainSuccess(true);
      setTimeout(() => {
        fetchData();
        setRetrainSuccess(false);
      }, 3000);
    } catch (e) {
      console.error('Retrain failed', e);
    } finally {
      setIsRetraining(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-card p-6 rounded-3xl border border-rose-500/20">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 text-rose-400 text-xs font-bold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Admin & ModelOps Telemetry Console</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Machine Learning Diagnostics & Governance
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry, model health monitoring, offline IR holdout benchmarks, and continuous retrain orchestration.
          </p>
        </div>

        {/* Retrain Action Button */}
        <div>
          <button
            onClick={handleRetrain}
            disabled={isRetraining}
            className="px-5 py-3 rounded-2xl bg-gradient-to-r from-rose-500 to-orange-500 hover:from-rose-400 hover:to-orange-400 disabled:opacity-50 text-white font-bold text-xs flex items-center gap-2 transition active:scale-95 shadow-xl shadow-rose-500/20"
          >
            <RefreshCw className={`w-4 h-4 ${isRetraining ? 'animate-spin' : ''}`} />
            <span>{isRetraining ? 'Retraining Pipeline...' : 'Trigger Pipeline Retrain'}</span>
          </button>
        </div>
      </div>

      {retrainSuccess && (
        <div className="p-4 rounded-2xl bg-teal-950/50 border border-teal-500/40 text-teal-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-400" />
          <span>Retrain pipeline executed successfully in background worker. Updated evaluation metrics refreshed!</span>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Shoppers</span>
            <Users className="w-4 h-4 text-teal-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {overview?.total_users || 0}
          </div>
          <div className="text-[11px] text-teal-400 font-medium">Clustered behavioral personas</div>
        </div>

        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Catalog Items</span>
            <ShoppingBag className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {overview?.total_products || 0}
          </div>
          <div className="text-[11px] text-cyan-400 font-medium">100% TF-IDF indexed</div>
        </div>

        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Telemetry Events</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {overview?.total_interactions || 0}
          </div>
          <div className="text-[11px] text-indigo-400 font-medium">Implicit feedback logged</div>
        </div>

        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Completed Orders</span>
            <Award className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {overview?.total_orders || 0}
          </div>
          <div className="text-[11px] text-amber-400 font-medium">FP-Growth basket source</div>
        </div>
      </div>

      {/* Interaction Distribution Breakdown */}
      {overview?.interaction_breakdown && (
        <section className="glass-card p-6 rounded-3xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-teal-400" />
            <span>Implicit Interaction Telemetry Breakdown</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {Object.entries(overview.interaction_breakdown).map(([type, count]) => (
              <div key={type} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400">{type}</span>
                <div className="text-base font-extrabold text-white mt-1">{count}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Model Benchmark Comparison Table (Academic Defense Table) */}
      <section className="glass-card p-6 rounded-3xl space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Award className="w-4 h-4 text-teal-400" />
            <span>Offline Information Retrieval (IR) Benchmark Table (Holdout Test Set)</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Standard RecSys evaluation protocol: Temporal Leave-Last-20% split with 1:99 negative item sampling.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                <th className="py-3 px-3">Model Architecture</th>
                <th className="py-3 px-3">Precision@5</th>
                <th className="py-3 px-3">Recall@5</th>
                <th className="py-3 px-3">NDCG@10</th>
                <th className="py-3 px-3">MAP@10</th>
                <th className="py-3 px-3">HitRate@10</th>
                <th className="py-3 px-3">Coverage %</th>
                <th className="py-3 px-3">Diversity (MMR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {metrics.map((m) => {
                const isHybrid = m.model_name.includes('Hybrid');
                return (
                  <tr
                    key={m.id}
                    className={`transition ${
                      isHybrid ? 'bg-teal-950/20 font-bold text-teal-300' : 'text-slate-300 hover:bg-slate-900/40'
                    }`}
                  >
                    <td className="py-3 px-3 font-sans font-semibold">
                      {m.model_name}
                      {isHybrid && (
                        <span className="ml-2 text-[10px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-400 uppercase font-bold">
                          Proposed
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3">{(m.precision_at_5 * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3">{(m.recall_at_5 * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3">{m.ndcg_at_10.toFixed(3)}</td>
                    <td className="py-3 px-3">{m.map_at_10.toFixed(3)}</td>
                    <td className="py-3 px-3">{(m.hit_rate_at_10 * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3">{m.catalog_coverage.toFixed(1)}%</td>
                    <td className="py-3 px-3">{m.diversity_score.toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
