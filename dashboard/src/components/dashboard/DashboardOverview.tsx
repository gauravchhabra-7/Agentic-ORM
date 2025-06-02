import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { MetricsGrid } from './MetricsGrid';
import { RecentComments } from './RecentComments';
import { ActivityFeed } from './ActivityFeed';
import { TrendChart } from './TrendChart';
import { apiService } from '../../services/api';
import type { Client } from '../../types';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface DashboardOverviewProps {
  selectedClient: Client | null;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ selectedClient }) => {
  // Fetch dashboard data
  const { 
    data: metricsData, 
    isLoading: metricsLoading, 
    error: metricsError,
    refetch: refetchMetrics 
  } = useQuery({
    queryKey: ['dashboard-metrics', selectedClient?.id],
    queryFn: () => selectedClient ? apiService.getDashboardMetrics(selectedClient.id) : null,
    enabled: !!selectedClient,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { 
    data: commentsData, 
    isLoading: commentsLoading 
  } = useQuery({
    queryKey: ['recent-comments', selectedClient?.id],
    queryFn: () => selectedClient ? apiService.getRecentComments(selectedClient.id, 10) : null,
    enabled: !!selectedClient,
    refetchInterval: 15000, // Refresh every 15 seconds for real-time feel
  });

  const { 
    data: activityData, 
    isLoading: activityLoading 
  } = useQuery({
    queryKey: ['activity-log', selectedClient?.id],
    queryFn: () => selectedClient ? apiService.getActivityLog(selectedClient.id, 10) : null,
    enabled: !!selectedClient,
    refetchInterval: 15000,
  });

  if (!selectedClient) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Client Selected</h3>
          <p className="text-gray-500">Please select a client from the dropdown to view the dashboard.</p>
        </div>
      </div>
    );
  }

  if (metricsError) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Dashboard</h3>
          <p className="text-gray-500 mb-4">There was an error loading the dashboard data.</p>
          <button
            onClick={() => refetchMetrics()}
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Dashboard Overview
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time monitoring for {selectedClient.name}
          </p>
        </div>
        
        {/* Real-time indicator */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Live</span>
          </div>
          <button
            onClick={() => {
              refetchMetrics();
            }}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Metrics */}
      <MetricsGrid 
        metrics={metricsData?.data || {
          total_comments: 0,
          positive_comments: 0,
          negative_comments: 0,
          neutral_comments: 0,
          auto_replied: 0,
          hidden_comments: 0,
          escalated_comments: 0,
          processing_time_avg: 0,
          response_rate: 0,
          automation_rate: 0,
        }} 
        isLoading={metricsLoading} 
      />

      {/* Trend Chart */}
      <div className="metric-card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Comment Sentiment Trends</h2>
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-600">Positive</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-gray-600">Negative</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-gray-600">Neutral</span>
            </div>
          </div>
        </div>
        <TrendChart clientId={selectedClient.id} />
      </div>

      {/* Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Comments */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Recent Comments</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View All
            </button>
          </div>
          <RecentComments 
            comments={commentsData?.data || []} 
            isLoading={commentsLoading} 
          />
        </div>

        {/* Activity Feed */}
        <div className="metric-card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              View All
            </button>
          </div>
          <ActivityFeed 
            activities={activityData?.data || []} 
            isLoading={activityLoading} 
          />
        </div>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <RefreshCw className="w-4 h-4 text-green-600" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">System Status</p>
              <p className="text-xs text-green-600">All systems operational</p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-4 h-4 text-blue-600" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-800">Processing Queue</p>
              <p className="text-xs text-blue-600">No pending items</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <RefreshCw className="w-4 h-4 text-purple-600 animate-spin" />
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-purple-800">Auto-Processing</p>
              <p className="text-xs text-purple-600">Active and monitoring</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
