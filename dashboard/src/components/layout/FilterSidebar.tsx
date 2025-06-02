import React from 'react';
import { 
  X, 
  Calendar, 
  Filter,
  RotateCcw,
  Instagram,
  Facebook,
  MessageCircle,
  Trash2
} from 'lucide-react';
import type { FilterOptions } from '../../types';

interface FilterSidebarProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  onClose: () => void;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  onFiltersChange,
  onClose,
}) => {
  
  const updateFilters = (updates: Partial<FilterOptions>) => {
    onFiltersChange({ ...filters, ...updates });
  };

  const resetFilters = () => {
    onFiltersChange({
      dateRange: {
        start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0],
      },
      platforms: ['instagram', 'facebook', 'facebook_ads'],
      sentiment: ['positive', 'negative', 'neutral'],
      status: ['pending', 'classified', 'processed'],
      urgency: ['low', 'medium', 'high'],
    });
  };

  const toggleArrayFilter = <T extends string>(
    array: T[], 
    value: T, 
    key: keyof FilterOptions
  ) => {
    const newArray = array.includes(value) 
      ? array.filter(item => item !== value)
      : [...array, value];
    updateFilters({ [key]: newArray });
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={resetFilters}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title="Reset Filters"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
        
        {/* Date Range Filter - FUNCTIONAL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Date Range
          </label>
          <div className="space-y-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Start Date</label>
              <input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) => updateFilters({
                  dateRange: { ...filters.dateRange, start: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) => updateFilters({
                  dateRange: { ...filters.dateRange, end: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Platform Filter - VISUAL DEMO */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Platforms
          </label>
          <div className="space-y-2">
            {[
              { id: 'instagram', label: 'Instagram', icon: Instagram, color: 'text-pink-600' },
              { id: 'facebook', label: 'Facebook', icon: Facebook, color: 'text-blue-600' },
              { id: 'facebook_ads', label: 'Facebook Ads', icon: MessageCircle, color: 'text-blue-500' },
            ].map(platform => (
              <label key={platform.id} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.platforms.includes(platform.id as any)}
                  onChange={() => toggleArrayFilter(filters.platforms, platform.id as any, 'platforms')}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <platform.icon className={`w-4 h-4 ${platform.color}`} />
                <span className="text-sm text-gray-700">{platform.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Comments/Messages Filter - VISUAL DEMO */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Comments / Messages
          </label>
          <div className="space-y-2">
            {[
              { id: 'positive', label: 'Positive', count: 789, color: 'bg-green-100 text-green-800' },
              { id: 'negative', label: 'Negative', count: 156, color: 'bg-red-100 text-red-800' },
              { id: 'neutral', label: 'Neutral', count: 302, color: 'bg-gray-100 text-gray-800' },
              { id: 'questions', label: 'Questions', count: 89, color: 'bg-blue-100 text-blue-800' },
            ].map(sentiment => (
              <label key={sentiment.id} className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={true} // Always checked for demo
                    onChange={() => {}} // No-op for demo
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">{sentiment.label}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${sentiment.color}`}>
                  {sentiment.count}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Keywords Filter - VISUAL DEMO */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Keywords
          </label>
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Search keywords..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <div className="flex flex-wrap gap-2 mt-2">
              {['shipping', 'quality', 'return', 'support'].map(keyword => (
                <span key={keyword} className="inline-flex items-center px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full">
                  {keyword}
                  <button className="ml-1 hover:text-primary-600">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Tags Filter - VISUAL DEMO */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Tags
          </label>
          <div className="space-y-2">
            {[
              { name: 'Urgent', count: 12, color: 'bg-red-100 text-red-800' },
              { name: 'Escalated', count: 5, color: 'bg-yellow-100 text-yellow-800' },
              { name: 'Auto-replied', count: 445, color: 'bg-green-100 text-green-800' },
              { name: 'Hidden', count: 23, color: 'bg-gray-100 text-gray-800' },
            ].map(tag => (
              <label key={tag.name} className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">{tag.name}</span>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${tag.color}`}>
                  {tag.count}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Sentiment Analysis - FUNCTIONAL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Sentiment
          </label>
          <div className="space-y-2">
            {[
              { id: 'positive', label: 'Positive', color: 'bg-green-100 text-green-800' },
              { id: 'negative', label: 'Negative', color: 'bg-red-100 text-red-800' },
              { id: 'neutral', label: 'Neutral', color: 'bg-gray-100 text-gray-800' },
            ].map(sentiment => (
              <label key={sentiment.id} className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.sentiment.includes(sentiment.id as any)}
                  onChange={() => toggleArrayFilter(filters.sentiment, sentiment.id as any, 'sentiment')}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className={`text-xs px-2 py-1 rounded-full ${sentiment.color}`}>
                  {sentiment.label}
                </span>
              </label>
            ))}
          </div>
        </div>

      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <button 
            onClick={() => {/* Apply filters - demo only */}}
            className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors duration-150"
          >
            Apply Filters
          </button>
          <button 
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors duration-150"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};