export interface Product {
  id: string;
  title: string;
  description: string;
  category_id: number;
  category_name?: string;
  subcategory?: string;
  brand: string;
  price: number;
  discount_percent: number;
  rating: number;
  rating_count: number;
  stock: number;
  image_url: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
}

export interface RecommendationExplanation {
  primary_factor: 'CONTENT_SIMILARITY' | 'COLLABORATIVE_FILTERING' | 'POPULAR_TRENDING' | 'FREQUENT_BUNDLE' | 'CATEGORY_INTEREST';
  reason_text: string;
  content_score: number;
  collaborative_score: number;
  popularity_score: number;
  final_score: number;
}

export interface RecommendedProduct {
  product: Product;
  score: number;
  explanation: RecommendationExplanation;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'USER' | 'ADMIN';
  age?: number;
  gender?: string;
  location?: string;
  preferred_categories: string[];
  created_at: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface ModelMetrics {
  id: string;
  model_version: string;
  model_name: string;
  precision_at_5: number;
  recall_at_5: number;
  precision_at_10: number;
  recall_at_10: number;
  ndcg_at_10: number;
  map_at_10: number;
  hit_rate_at_10: number;
  catalog_coverage: number;
  diversity_score: number;
  training_sample_count: number;
  training_duration_sec: number;
  created_at: string;
}

export interface AnalyticsOverview {
  total_users: int;
  total_products: int;
  total_orders: int;
  total_interactions: int;
  active_models: string[];
  interaction_breakdown: Record<string, number>;
  top_selling_categories: Array<{ category: string; interactions: number }>;
}
