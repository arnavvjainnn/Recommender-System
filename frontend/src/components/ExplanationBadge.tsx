import React from 'react';
import { Sparkles, Layers, Flame, PackagePlus, Compass } from 'lucide-react';
import { RecommendationExplanation } from '../types';

interface Props {
  explanation?: RecommendationExplanation;
  className?: string;
}

export const ExplanationBadge: React.FC<Props> = ({ explanation, className = '' }) => {
  if (!explanation) return null;

  const getBadgeConfig = () => {
    switch (explanation.primary_factor) {
      case 'COLLABORATIVE_FILTERING':
        return {
          icon: <Layers className="w-3.5 h-3.5 text-indigo-400" />,
          label: 'Community Match',
          bg: 'bg-indigo-950/60 border-indigo-500/30 text-indigo-300',
        };
      case 'CONTENT_SIMILARITY':
        return {
          icon: <Sparkles className="w-3.5 h-3.5 text-teal-400" />,
          label: 'Similar Specs',
          bg: 'bg-teal-950/60 border-teal-500/30 text-teal-300',
        };
      case 'FREQUENT_BUNDLE':
        return {
          icon: <PackagePlus className="w-3.5 h-3.5 text-amber-400" />,
          label: 'Frequent Bundle',
          bg: 'bg-amber-950/60 border-amber-500/30 text-amber-300',
        };
      case 'CATEGORY_INTEREST':
        return {
          icon: <Compass className="w-3.5 h-3.5 text-emerald-400" />,
          label: 'Your Interest',
          bg: 'bg-emerald-950/60 border-emerald-500/30 text-emerald-300',
        };
      case 'POPULAR_TRENDING':
      default:
        return {
          icon: <Flame className="w-3.5 h-3.5 text-rose-400" />,
          label: 'Trending Momentum',
          bg: 'bg-rose-950/60 border-rose-500/30 text-rose-300',
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <div
      title={explanation.reason_text}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border backdrop-blur-md cursor-help ${config.bg} ${className}`}
    >
      {config.icon}
      <span>{config.label}</span>
      {explanation.final_score > 0 && (
        <span className="opacity-70 text-[10px]">
          {Math.round(explanation.final_score * 100)}%
        </span>
      )}
    </div>
  );
};
