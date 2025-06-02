// Dashboard Types for ORM-MVP
export interface Client {
  id: string;
  name: string;
  status: 'active' | 'inactive';
  plan: 'basic' | 'pro' | 'enterprise';
}

export interface Comment {
  comment_id: string;
  client_id: string;
  platform: 'instagram' | 'facebook' | 'facebook_ads';
  text: string;
  author_name: string;
  author_id: string;
  created_time: string;
  like_count: number;
  status: 'pending' | 'classified' | 'processed';
  classification?: Classification;
  action_taken?: 'replied' | 'hidden' | 'escalated' | 'ignored';
  reply_sent?: boolean;
  hidden?: boolean;
  escalated?: boolean;
}

export interface Classification {
  sentiment: 'positive' | 'negative' | 'neutral';
  urgency: 'low' | 'medium' | 'high';
  intent: 'question' | 'complaint' | 'compliment' | 'spam' | 'general';
  toxicity_score: number;
  confidence: number;
  requires_response: boolean;
  suggested_action: 'reply' | 'hide' | 'escalate' | 'ignore';
}

export interface DashboardMetrics {
  total_comments: number;
  positive_comments: number;
  negative_comments: number;
  neutral_comments: number;
  auto_replied: number;
  hidden_comments: number;
  escalated_comments: number;
  processing_time_avg: number;
  response_rate: number;
  automation_rate: number;
}

export interface ActivityLog {
  id: string;
  timestamp: string;
  action_type: 'reply_sent' | 'comment_hidden' | 'comment_escalated' | 'classification_completed';
  comment_id: string;
  details: {
    message?: string;
    reason?: string;
    confidence?: number;
  };
}

export interface FilterOptions {
  dateRange: {
    start: string;
    end: string;
  };
  platforms: ('instagram' | 'facebook' | 'facebook_ads')[];
  sentiment: ('positive' | 'negative' | 'neutral')[];
  status: ('pending' | 'classified' | 'processed')[];
  urgency: ('low' | 'medium' | 'high')[];
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  errors?: string[];
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  timestamp?: string;
}

export interface TrendData {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}