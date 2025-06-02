import React from 'react';
import { 
  MessageCircle, 
  TrendingUp, 
  TrendingDown, 
  Bot,
  Shield,
  AlertTriangle,
  Clock,
  Zap,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import type { DashboardMetrics } from '../../types';

interface MetricsGridProps {
  metrics: DashboardMetrics;
  isLoading?: boolean;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  subtitle?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  icon: Icon, 
  color, 
  bgColor, 
  trend,
  subtitle 
}) => {
  const getTrendIcon = () => {
    if (!trend) return null;
    
    switch (trend.direction) {
      case 'up': return <ArrowUp className="w-3 h-3" />;
      case 'down': return <ArrowDown className="w-3 h-3" />;
      default: return <Minus className="w-3 h-3" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return '';
    
    switch (trend.direction) {
      case 'up': return 'text-green-600';
      case 'down': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="metric-card group">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${bgColor}`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              {subtitle && (
                <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
              )}
            </div>
          </div>
        </div>
        
        {trend && (
          <div className={`flex items-center space-x-1 ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="text-sm font-medium">{trend.value}%</span>
          </div>
        )}
      </div>
      
      {trend && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500">{trend.label}</p>
        </div>
      )}
    </div>
  );
};

export const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="metric-card animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-gray-200 rounded-lg"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-20 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const metricCards = [
    {
      title: 'Total Comments',
      value: metrics.total_comments.toLocaleString(),
      icon: MessageCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      trend: {
        value: 12,
        label: 'vs last 30 days',
        direction: 'up' as const,
      },
      subtitle: 'Last 30 days'
    },
    {
      title: 'Positive Sentiment',
      value: metrics.positive_comments.toLocaleString(),
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      trend: {
        value: 8,
        label: 'vs last period',
        direction: 'up' as const,
      },
      subtitle: `${((metrics.positive_comments / metrics.total_comments) * 100).toFixed(1)}% of total`
    },
    {
      title: 'Negative/Toxic',
      value: metrics.negative_comments.toLocaleString(),
      icon: TrendingDown,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      trend: {
        value: 15,
        label: 'reduction this month',
        direction: 'down' as const,
      },
      subtitle: `${((metrics.negative_comments / metrics.total_comments) * 100).toFixed(1)}% of total`
    },
    {
      title: 'Auto-Replied',
      value: metrics.auto_replied.toLocaleString(),
      icon: Bot,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      trend: {
        value: 25,
        label: 'efficiency improvement',
        direction: 'up' as const,
      },
      subtitle: `${((metrics.auto_replied / metrics.total_comments) * 100).toFixed(1)}% automation rate`
    },
    {
      title: 'Hidden/Moderated',
      value: metrics.hidden_comments.toLocaleString(),
      icon: Shield,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      trend: {
        value: 5,
        label: 'vs last month',
        direction: 'down' as const,
      },
      subtitle: 'Toxic content blocked'
    },
    {
      title: 'Escalated to Human',
      value: metrics.escalated_comments.toLocaleString(),
      icon: AlertTriangle,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      trend: {
        value: 3,
        label: 'requiring attention',
        direction: 'neutral' as const,
      },
      subtitle: 'High-priority issues'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {metricCards.map((card, index) => (
          <MetricCard key={index} {...card} />
        ))}
      </div>

      {/* Performance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="metric-card">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.processing_time_avg}s</p>
              <p className="text-xs text-gray-500 mt-1">From comment to action</p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-green-100">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Response Rate</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.response_rate}%</p>
              <p className="text-xs text-gray-500 mt-1">Comments receiving replies</p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Automation Rate</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.automation_rate}%</p>
              <p className="text-xs text-gray-500 mt-1">Fully automated actions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};