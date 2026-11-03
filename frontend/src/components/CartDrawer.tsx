import React, { useState } from 'react';
import { X, Trash2, Plus, Minus, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useCart } from '../context/CartContext';

export const CartDrawer: React.FC = () => {
  const { cart, isCartOpen, setIsCartOpen, updateQuantity, removeFromCart, totalPrice, checkout } = useCart();
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);

  if (!isCartOpen) return null;

  const handleCheckout = async () => {
    setIsCheckingOut(true);
    try {
      await checkout();
      setOrderComplete(true);
      setTimeout(() => {
        setOrderComplete(false);
        setIsCartOpen(false);
      }, 2500);
    } catch (e) {
      console.error('Checkout error', e);
    } finally {
      setIsCheckingOut(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        onClick={() => setIsCartOpen(false)}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
      />

      {/* Drawer */}
      <div className="relative w-full max-w-md h-full bg-[#0F172A] border-l border-slate-800 shadow-2xl flex flex-col z-10">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="font-bold text-base text-white">Your Shopping Cart</h2>
          <button
            onClick={() => setIsCartOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {orderComplete ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
              <CheckCircle2 className="w-16 h-16 text-teal-400 animate-bounce" />
              <h3 className="text-lg font-bold text-white">Order Simulated Successfully!</h3>
              <p className="text-xs text-slate-400 max-w-xs">
                Your purchase interaction has been logged into the recommendation engine. Models will incorporate this in next personalization cycles!
              </p>
            </div>
          ) : cart.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
              <p className="text-sm">Your cart is empty.</p>
              <p className="text-xs text-slate-600 mt-1">Add items from recommendations to build your setup!</p>
            </div>
          ) : (
            cart.map(({ product, quantity }) => (
              <div
                key={product.id}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800/80"
              >
                <img
                  src={product.image_url}
                  alt={product.title}
                  className="w-16 h-16 rounded-lg object-cover bg-slate-950 flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-semibold text-slate-200 truncate">{product.title}</h4>
                  <div className="text-xs text-teal-400 font-bold mt-1">
                    ${product.price.toFixed(2)}
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => updateQuantity(product.id, quantity - 1)}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="text-xs font-semibold text-white px-1.5">{quantity}</span>
                    <button
                      onClick={() => updateQuantity(product.id, quantity + 1)}
                      className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => removeFromCart(product.id)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {cart.length > 0 && !orderComplete && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/60 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-400">Total Subtotal</span>
              <span className="text-lg font-bold text-white">${totalPrice.toFixed(2)}</span>
            </div>
            <button
              onClick={handleCheckout}
              disabled={isCheckingOut}
              className="w-full py-3 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition active:scale-[0.98] shadow-lg shadow-teal-500/25"
            >
              <span>{isCheckingOut ? 'Recording Purchase...' : 'Simulate Instant Checkout'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
