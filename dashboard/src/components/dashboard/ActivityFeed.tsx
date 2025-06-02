import React from 'react';
import { 
  Bot, 
  EyeOff, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  MessageCircle,
  Zap
} from 'lucide-react';
import type { ActivityLog } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface ActivityFeedProps {
  activities: ActivityLog[];
  isLoading?: boolean;
}

const getActivityIcon = (actionType: string) => {
  switch (actionType) {
    case 'reply_sent': return Bot;
    case 'comment_hidden': return EyeOff;
    case 'comment_escalated': return AlertTriangle;
    case 'classification_completed': return CheckCircle;
    default: return Clock;
  }
};

const getActivityColor = (actionType: string) => {
  switch (actionType) {
    case 'reply_sent': return 'text-green-600 bg-green-100';
    case 'comment_hidden': return 'text-orange-600 bg-orange-100';
    case 'comment_escalated': return 'text-red-600 bg-red-100';
    case 'classification_completed': return 'text-blue-600 bg-blue-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const getActivityTitle = (actionType: string) => {
  switch (actionType) {
    case 'reply_sent': return 'Auto-Reply Sent';
    case 'comment_hidden': return 'Comment Hidden';
    case 'comment_escalated': return 'Escalated to Human';
    case 'classification_completed': return 'Comment Classified';
    default: return 'Activity';
  }
};

const getActivityDescription = (activity: ActivityLog) => {
  const { action_type, details } = activity;
  
  switch (action_type) {
    case 'reply_sent':
      return `Automated response sent with ${details.confidence}% confidence`;
    case 'comment_hidden':
      return `Hidden due to: ${details.reason}`;
    case 'comment_escalated':
      return `Escalated: ${details.reason}`;
    case 'classification_completed':
      return `Analysis completed with ${details.confidence}% confidence`;
    default:
      return 'System activity recorded';
  }
};

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ activities, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="flex space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Zap className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-sm font-medium text-gray-900 mb-2">No Recent Activity</h3>
        <p className="text-sm text-gray-500">Automated actions will appear here as they occur.</p>
      </div>
    );
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {activities.map((activity, activityIdx) => {
          const ActivityIcon = getActivityIcon(activity.action_type);
          const timeAgo = formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true });
          const isLast = activityIdx === activities.length - 1;

          return (
            <li key={activity.id}>
              <div className="relative pb-8">
                {/* Connecting Line */}
                {!isLast && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}

                <div className="relative flex space-x-3">
                  {/* Activity Icon */}
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${getActivityColor(activity.action_type)}`}>
                    <ActivityIcon className="w-4 h-4" />
                  </div>

                  {/* Activity Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {getActivityTitle(activity.action_type)}
                        </p>
                        <p className="text-sm text-gray-500">
                          {getActivityDescription(activity)}
                        </p>
                      </div>
                      <div className="text-right text-xs text-gray-400">
                        {timeAgo}
                      </div>
                    </div>

                    {/* Comment ID Reference */}
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                        <MessageCircle className="w-3 h-3 mr-1" />
                        #{activity.comment_id.slice(-8)}
                      </span>
                    </div>

                    {/* Additional Details */}
                    {activity.details.message && (
                      <div className="mt-2 p-2 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-600 italic">
                          "{activity.details.message.length > 80 
                            ? `${activity.details.message.substring(0, 80)}...` 
                            : activity.details.message}"
                        </p>
                      </div>
                    )}

                    {/* Confidence Score */}
                    {activity.details.confidence && (
                      <div className="mt-2 flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                          <div 
                            className={`h-1.5 rounded-full ${
                              activity.details.confidence >= 90 ? 'bg-green-500' :
                              activity.details.confidence >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${activity.details.confidence}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">
                          {activity.details.confidence}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {/* Activity Summary */}
      <div className="mt-6 p-4 bg-primary-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-primary-600" />
            <span className="text-sm font-medium text-primary-800">
              System Performance
            </span>
          </div>
          <div className="text-right">
            <p className="text-sm font-semibold text-primary-900">
              {activities.length} actions in last hour
            </p>
            <p className="text-xs text-primary-600">
              95% automated processing
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};