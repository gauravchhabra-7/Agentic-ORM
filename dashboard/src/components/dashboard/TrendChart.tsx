import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { TrendData } from '../../types';

interface TrendChartProps {
  clientId: string;
}

// Mock trend data for demo - in production this would come from API
const generateMockTrendData = (): TrendData[] => {
  const data: TrendData[] = [];
  const today = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    // Generate realistic looking data with some randomness
    const basePositive = 30 + Math.random() * 20;
    const baseNegative = 5 + Math.random() * 10;
    const baseNeutral = 15 + Math.random() * 15;
    
    data.push({
      date: date.toISOString().split('T')[0],
      positive: Math.round(basePositive),
      negative: Math.round(baseNegative),
      neutral: Math.round(baseNeutral),
      total: Math.round(basePositive + baseNegative + baseNeutral),
    });
  }
  
  return data;
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900 mb-2">
          {new Date(label).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
          })}
        </p>
        <div className="space-y-1">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-xs text-gray-600">Positive</span>
            </div>
            <span className="text-xs font-medium text-gray-900">{data.positive}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-xs text-gray-600">Negative</span>
            </div>
            <span className="text-xs font-medium text-gray-900">{data.negative}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
              <span className="text-xs text-gray-600">Neutral</span>
            </div>
            <span className="text-xs font-medium text-gray-900">{data.neutral}</span>
          </div>
          <div className="pt-1 border-t border-gray-100 mt-2">
            <div className="flex items-center justify-between space-x-4">
              <span className="text-xs font-medium text-gray-700">Total</span>
              <span className="text-xs font-bold text-gray-900">{data.total}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export const TrendChart: React.FC<TrendChartProps> = ({ clientId }) => {
  const data = generateMockTrendData();

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date"
            tick={{ fontSize: 12, fill: '#6b7280' }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          
          <Line
            type="monotone"
            dataKey="positive"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#10b981' }}
          />
          <Line
            type="monotone"
            dataKey="negative"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#ef4444' }}
          />
          <Line
            type="monotone"
            dataKey="neutral"
            stroke="#6b7280"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#6b7280' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};