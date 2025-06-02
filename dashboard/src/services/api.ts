import type { Client, Comment, DashboardMetrics, ActivityLog, FilterOptions, ApiResponse } from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/dev'
  : 'http://localhost:3001'; // Local dev server if needed

const USE_MOCK_DATA = !import.meta.env.PROD; // Use mock data in development

class ApiService {
  private baseUrl: string;
  private useMock: boolean;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.useMock = USE_MOCK_DATA;
  }

  // Generic API call method
  private async apiCall<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  // Client Management
  async getClients(): Promise<ApiResponse<Client[]>> {
    if (this.useMock) {
      return this.getMockClients();
    }
    return this.apiCall<Client[]>('/clients');
  }

  // Dashboard Metrics
  async getDashboardMetrics(clientId: string, filters?: Partial<FilterOptions>): Promise<ApiResponse<DashboardMetrics>> {
    if (this.useMock) {
      return this.getMockDashboardMetrics(clientId);
    }
    
    const params = new URLSearchParams();
    if (filters?.dateRange) {
      params.append('start_date', filters.dateRange.start);
      params.append('end_date', filters.dateRange.end);
    }
    
    return this.apiCall<DashboardMetrics>(`/metrics/${clientId}?${params.toString()}`);
  }

  // Comments
  async getRecentComments(clientId: string, limit: number = 50): Promise<ApiResponse<Comment[]>> {
    if (this.useMock) {
      return this.getMockRecentComments(clientId, limit);
    }
    return this.apiCall<Comment[]>(`/comments/recent/${clientId}?limit=${limit}`);
  }

  // Activity Log
  async getActivityLog(clientId: string, limit: number = 20): Promise<ApiResponse<ActivityLog[]>> {
    if (this.useMock) {
      return this.getMockActivityLog(clientId, limit);
    }
    return this.apiCall<ActivityLog[]>(`/activity/${clientId}?limit=${limit}`);
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    if (this.useMock) {
      return {
        status: 'success',
        data: {
          status: 'healthy',
          timestamp: new Date().toISOString(),
        },
      };
    }
    return this.apiCall<{ status: string; timestamp: string }>('/health');
  }

  // Mock Data Methods (for development)
  private getMockClients(): Promise<ApiResponse<Client[]>> {
    return Promise.resolve({
      status: 'success',
      data: [
        {
          id: 'demo_client_001',
          name: 'Annus Mirabilis',
          status: 'active',
          plan: 'pro',
        },
        {
          id: 'client_002',
          name: 'Demo Client 2',
          status: 'active',
          plan: 'basic',
        },
        {
          id: 'client_003',
          name: 'Enterprise Demo',
          status: 'inactive',
          plan: 'enterprise',
        },
      ],
    });
  }

  private getMockDashboardMetrics(clientId: string): Promise<ApiResponse<DashboardMetrics>> {
    // Generate realistic demo data
    const baseMetrics = {
      total_comments: 1247,
      positive_comments: 789,
      negative_comments: 156,
      neutral_comments: 302,
      auto_replied: 445,
      hidden_comments: 23,
      escalated_comments: 12,
      processing_time_avg: 2.3,
      response_rate: 89.2,
      automation_rate: 95.1,
    };

    return Promise.resolve({
      status: 'success',
      data: baseMetrics,
    });
  }

  private getMockRecentComments(clientId: string, limit: number): Promise<ApiResponse<Comment[]>> {
    const mockComments: Comment[] = [
      {
        comment_id: 'comment_001',
        client_id: clientId,
        platform: 'instagram',
        text: 'Love this product! Amazing quality and fast shipping. Highly recommend! 😍',
        author_name: 'Sarah Johnson',
        author_id: 'user_001',
        created_time: '2025-06-02T10:30:00Z',
        like_count: 5,
        status: 'processed',
        classification: {
          sentiment: 'positive',
          urgency: 'low',
          intent: 'compliment',
          toxicity_score: 0,
          confidence: 95,
          requires_response: true,
          suggested_action: 'reply',
        },
        action_taken: 'replied',
        reply_sent: true,
      },
      {
        comment_id: 'comment_002',
        client_id: clientId,
        platform: 'instagram',
        text: 'Hi, I have a question about the return policy. How long do I have to return an item?',
        author_name: 'Mike Chen',
        author_id: 'user_002',
        created_time: '2025-06-02T09:15:00Z',
        like_count: 0,
        status: 'processed',
        classification: {
          sentiment: 'neutral',
          urgency: 'medium',
          intent: 'question',
          toxicity_score: 0,
          confidence: 88,
          requires_response: true,
          suggested_action: 'reply',
        },
        action_taken: 'replied',
        reply_sent: true,
      },
      {
        comment_id: 'comment_003',
        client_id: clientId,
        platform: 'facebook',
        text: 'This is the worst product I have ever bought. Complete waste of money! Never buying again.',
        author_name: 'John Smith',
        author_id: 'user_003',
        created_time: '2025-06-02T08:45:00Z',
        like_count: 0,
        status: 'processed',
        classification: {
          sentiment: 'negative',
          urgency: 'high',
          intent: 'complaint',
          toxicity_score: 6,
          confidence: 92,
          requires_response: true,
          suggested_action: 'escalate',
        },
        action_taken: 'escalated',
        escalated: true,
      },
      {
        comment_id: 'comment_004',
        client_id: clientId,
        platform: 'instagram',
        text: 'Spam spam spam buy my product click here now!!! 🚫🚫🚫',
        author_name: 'SpamBot123',
        author_id: 'spam_001',
        created_time: '2025-06-02T07:30:00Z',
        like_count: 0,
        status: 'processed',
        classification: {
          sentiment: 'negative',
          urgency: 'low',
          intent: 'spam',
          toxicity_score: 8,
          confidence: 99,
          requires_response: false,
          suggested_action: 'hide',
        },
        action_taken: 'hidden',
        hidden: true,
      },
      {
        comment_id: 'comment_005',
        client_id: clientId,
        platform: 'facebook_ads',
        text: 'When will my order ship? I ordered 3 days ago and still no tracking info.',
        author_name: 'Lisa Wilson',
        author_id: 'user_005',
        created_time: '2025-06-02T06:20:00Z',
        like_count: 2,
        status: 'classified',
        classification: {
          sentiment: 'neutral',
          urgency: 'medium',
          intent: 'question',
          toxicity_score: 1,
          confidence: 85,
          requires_response: true,
          suggested_action: 'reply',
        },
      },
    ];

    return Promise.resolve({
      status: 'success',
      data: mockComments.slice(0, limit),
    });
  }

  private getMockActivityLog(clientId: string, limit: number): Promise<ApiResponse<ActivityLog[]>> {
    const mockActivity: ActivityLog[] = [
      {
        id: 'activity_001',
        timestamp: '2025-06-02T10:35:00Z',
        action_type: 'reply_sent',
        comment_id: 'comment_001',
        details: {
          message: 'Thank you so much for the kind words! We\'re thrilled you had a great experience. 🎉',
          confidence: 95,
        },
      },
      {
        id: 'activity_002',
        timestamp: '2025-06-02T09:20:00Z',
        action_type: 'reply_sent',
        comment_id: 'comment_002',
        details: {
          message: 'Hi Mike! You have 30 days to return any item from the purchase date. Check your email for our full return policy. 😊',
          confidence: 88,
        },
      },
      {
        id: 'activity_003',
        timestamp: '2025-06-02T08:50:00Z',
        action_type: 'comment_escalated',
        comment_id: 'comment_003',
        details: {
          reason: 'High urgency negative sentiment detected',
          confidence: 92,
        },
      },
      {
        id: 'activity_004',
        timestamp: '2025-06-02T07:35:00Z',
        action_type: 'comment_hidden',
        comment_id: 'comment_004',
        details: {
          reason: 'High toxicity score (8/10) - Spam content detected',
          confidence: 99,
        },
      },
      {
        id: 'activity_005',
        timestamp: '2025-06-02T06:25:00Z',
        action_type: 'classification_completed',
        comment_id: 'comment_005',
        details: {
          confidence: 85,
        },
      },
    ];

    return Promise.resolve({
      status: 'success',
      data: mockActivity.slice(0, limit),
    });
  }
}

export const apiService = new ApiService();