import axios from 'axios';
import { Product, Category, RecommendedProduct, User, CartItem, ModelMetrics, AnalyticsOverview } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-inject JWT token if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Client session manager for guest telemetry
export const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('recommendai_session_id');
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substring(2, 12);
    sessionStorage.setItem('recommendai_session_id', sessionId);
  }
  return sessionId;
};

export const authApi = {
  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (data: { email: string; password: string; full_name: string; preferred_categories?: string[] }) => {
    const res = await api.post('/auth/register', data);
    return res.data;
  },
  getMe: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  updatePreferences: async (categories: string[], minPrice = 0, maxPrice?: number) => {
    const res = await api.post('/auth/preferences', { categories, min_price: minPrice, max_price: maxPrice });
    return res.data;
  },
};

export const productsApi = {
  getAll: async (params?: { page?: number; limit?: number; category_id?: number; sort_by?: string; brand?: string }) => {
    const res = await api.get('/products', { params });
    return res.data;
  },
  getById: async (id: string): Promise<Product> => {
    const res = await api.get(`/products/${id}`);
    return res.data;
  },
  search: async (q: string, limit = 12): Promise<Product[]> => {
    const res = await api.get('/products/search', { params: { q, limit } });
    return res.data;
  },
  getCategories: async (): Promise<Category[]> => {
    const res = await api.get('/products/categories');
    return res.data;
  },
};

export const interactionsApi = {
  log: async (productId: string, interactionType: string) => {
    try {
      await api.post('/interactions', {
        product_id: productId,
        interaction_type: interactionType,
        session_id: getSessionId(),
      });
    } catch (e) {
      console.warn('Telemetry log suppressed', e);
    }
  },
  rate: async (productId: string, ratingValue: number, reviewText?: string) => {
    const res = await api.post('/ratings', {
      product_id: productId,
      rating_value: ratingValue,
      review_text: reviewText,
    });
    return res.data;
  },
  checkout: async (items: CartItem[], shippingAddress?: string) => {
    const payload = {
      items: items.map((i) => ({ product_id: i.product.id, quantity: i.quantity })),
      shipping_address: shippingAddress || 'Campus Tech Park, Demo Address',
    };
    const res = await api.post('/cart/checkout', payload);
    return res.data;
  },
};

export const recommendationsApi = {
  getPersonalized: async (limit = 10): Promise<RecommendedProduct[]> => {
    const res = await api.get('/recommendations/personalized', {
      params: { session_id: getSessionId(), limit },
    });
    return res.data;
  },
  getSimilar: async (productId: string, limit = 6): Promise<RecommendedProduct[]> => {
    const res = await api.get(`/recommendations/similar/${productId}`, { params: { limit } });
    return res.data;
  },
  getFrequentlyBought: async (productId: string, limit = 4): Promise<RecommendedProduct[]> => {
    const res = await api.get(`/recommendations/frequently-bought/${productId}`, { params: { limit } });
    return res.data;
  },
  getTrending: async (limit = 10): Promise<RecommendedProduct[]> => {
    const res = await api.get('/recommendations/trending', { params: { limit } });
    return res.data;
  },
  getPopular: async (limit = 10): Promise<RecommendedProduct[]> => {
    const res = await api.get('/recommendations/popular', { params: { limit } });
    return res.data;
  },
  getColdStart: async (categories: string[], limit = 10): Promise<RecommendedProduct[]> => {
    const res = await api.get('/recommendations/cold-start', {
      params: { categories, session_id: getSessionId(), limit },
    });
    return res.data;
  },
};

export const adminApi = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const res = await api.get('/admin/analytics/overview');
    return res.data;
  },
  getModelMetrics: async (): Promise<ModelMetrics[]> => {
    const res = await api.get('/admin/model-metrics');
    return res.data;
  },
  retrain: async (config?: any) => {
    const res = await api.post('/admin/retrain', config || {});
    return res.data;
  },
};

export default api;
