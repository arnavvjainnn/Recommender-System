import React, { useState } from 'react';
import { Sparkles, Check, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/api';

const AVAILABLE_CATEGORIES = [
  { name: 'Gaming', desc: 'Mechanical keyboards, 240Hz OLEDs, ultra-light mice' },
  { name: 'Computing', desc: 'M3 Pro laptops, Thunderbolt hubs, high-speed NVMe SSDs' },
  { name: 'Audio', desc: 'Active noise cancellation headphones, studio XLR interfaces' },
  { name: 'Wearables', desc: 'Titanium smartwatches, health tracking smart rings' },
  { name: 'Desk Setup', desc: 'ScreenBar lights, heavy-duty monitor arms, ergonomic chairs' },
  { name: 'Cameras & Video', desc: 'Full-frame 4K mirrorless cameras, lenses, Stream Decks' },
];

interface Props {
  onCompleted?: (categories: string[]) => void;
}

export const OnboardingModal: React.FC<Props> = ({ onCompleted }) => {
  const { showOnboarding, setShowOnboarding, user, refreshUser } = useAuth();
  const [selected, setSelected] = useState<string[]>(['Gaming', 'Computing']);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!showOnboarding) return null;

  const toggleCategory = (catName: string) => {
    if (selected.includes(catName)) {
      setSelected(selected.filter((c) => c !== catName));
    } else {
      setSelected([...selected, catName]);
    }
  };

  const handleSubmit = async () => {
    if (selected.length === 0) return;
    setIsSubmitting(true);
    try {
      if (user) {
        await authApi.updatePreferences(selected);
        await refreshUser();
      }
      setShowOnboarding(false);
      if (onCompleted) {
        onCompleted(selected);
      }
    } catch (e) {
      console.error('Failed to save onboarding preferences', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        onClick={() => setShowOnboarding(false)}
        className="fixed inset-0 bg-black/75 backdrop-blur-md transition-opacity"
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-lg glass-panel p-6 rounded-3xl border border-teal-500/30 shadow-2xl shadow-teal-950/50 z-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-teal-400 mb-1">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Personalize Your Feed (Cold-Start)
          </h2>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Select at least 1 or 2 categories you're interested in. Our hybrid recommender will synthesize immediate candidate vectors!
          </p>
        </div>

        {/* Category Selection Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {AVAILABLE_CATEGORIES.map((cat) => {
            const isSelected = selected.includes(cat.name);
            return (
              <div
                key={cat.name}
                onClick={() => toggleCategory(cat.name)}
                className={`p-3 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                  isSelected
                    ? 'bg-teal-950/40 border-teal-500 text-white shadow-md shadow-teal-500/10'
                    : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs">{cat.name}</span>
                  <div
                    className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                      isSelected ? 'bg-teal-500 text-slate-950 font-bold' : 'border border-slate-700'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 mt-1 line-clamp-1">{cat.desc}</p>
              </div>
            );
          })}
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={selected.length === 0 || isSubmitting}
          className="w-full py-3 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-40 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition active:scale-[0.98] shadow-lg shadow-teal-500/25"
        >
          <span>{isSubmitting ? 'Updating Recommender...' : `Apply Preferences (${selected.length} Selected)`}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
