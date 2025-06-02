import React from 'react';
import { 
  Instagram, 
  Facebook, 
  MessageCircle, 
  Heart,
  Reply,
  EyeOff,
  AlertTriangle,
  Clock,
  Bot
} from 'lucide-react';
import type { Comment } from '../../types';
import { formatDistanceToNow } from 'date-fns';

interface RecentCommentsProps {
  comments: Comment[];
  isLoading?: boolean;
}

const getPlatformIcon = (platform: string) => {
  switch (platform) {
    case 'instagram': return Instagram;
    case 'facebook': return Facebook;
    case 'facebook_ads': return MessageCircle;
    default: return MessageCircle;
  }
};

const getPlatformColor = (platform: string) => {
  switch (platform) {
    case 'instagram': return 'text-pink-600 bg-pink-100';
    case 'facebook': return 'text-blue-600 bg-blue-100';
    case 'facebook_ads': return 'text-blue-500 bg-blue-50';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const getSentimentColor = (sentiment: string) => {
  switch (sentiment) {
    case 'positive': return 'text-green-700 bg-green-100';
    case 'negative': return 'text-red-700 bg-red-100';
    case 'neutral': return 'text-gray-700 bg-gray-100';
    default: return 'text-gray-700 bg-gray-100';
  }
};

const getActionIcon = (action: string) => {
  switch (action) {
    case 'replied': return Bot;
    case 'hidden': return EyeOff;
    case 'escalated': return AlertTriangle;
    default: return Clock;
  }
};

const getActionColor = (action: string) => {
  switch (action) {
    case 'replied': return 'text-green-600 bg-green-100';
    case 'hidden': return 'text-orange-600 bg-orange-100';
    case 'escalated': return 'text-red-600 bg-red-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

export const RecentComments: React.FC<RecentCommentsProps> = ({ comments, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="flex space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                <div className="flex space-x-2">
                  <div className="h-5 bg-gray-200 rounded w-16"></div>
                  <div className="h-5 bg-gray-200 rounded w-16"></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (comments.length === 0) {
    return (
      <div className="text-center py-8">
        <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-sm font-medium text-gray-900 mb-2">No Recent Comments</h3>
        <p className="text-sm text-gray-500">Comments will appear here as they are processed.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {comments.map((comment) => {
        const PlatformIcon = getPlatformIcon(comment.platform);
        const ActionIcon = getActionIcon(comment.action_taken || 'pending');
        const timeAgo = formatDistanceToNow(new Date(comment.created_time), { addSuffix: true });

        return (
          <div key={comment.comment_id} className="group">
            <div className="flex space-x-3">
              {/* Platform Icon */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${getPlatformColor(comment.platform)}`}>
                <PlatformIcon className="w-4 h-4" />
              </div>

              {/* Comment Content */}
              <div className="flex-1 min-w-0">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {comment.author_name}
                    </span>
                    <span className="text-xs text-gray-500">
                      {timeAgo}
                    </span>
                  </div>
                  
                  {/* Action Status */}
                  {comment.action_taken && (
                    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActionColor(comment.action_taken)}`}>
                      <ActionIcon className="w-3 h-3 mr-1" />
                      {comment.action_taken}
                    </div>
                  )}
                </div>

                {/* Comment Text */}
                <p className="text-sm text-gray-800 mb-3 leading-relaxed">
                  {comment.text.length > 150 
                    ? `${comment.text.substring(0, 150)}...` 
                    : comment.text
                  }
                </p>

                {/* Engagement & Classification */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    {comment.like_count > 0 && (
                      <div className="flex items-center space-x-1">
                        <Heart className="w-3 h-3" />
                        <span>{comment.like_count}</span>
                      </div>
                    )}
                    
                    <span className="capitalize">{comment.platform.replace('_', ' ')}</span>
                  </div>

                  {/* Classification Badges */}
                  <div className="flex items-center space-x-2">
                    {comment.classification && (
                      <>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(comment.classification.sentiment)}`}>
                          {comment.classification.sentiment}
                        </span>
                        
                        {comment.classification.urgency !== 'low' && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            comment.classification.urgency === 'high' 
                              ? 'text-red-700 bg-red-100' 
                              : 'text-yellow-700 bg-yellow-100'
                          }`}>
                            {comment.classification.urgency}
                          </span>
                        )}

                        {comment.classification.toxicity_score >= 6 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium text-orange-700 bg-orange-100">
                            Toxic: {comment.classification.toxicity_score}/10
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Reply Preview */}
                {comment.reply_sent && (
                  <div className="mt-3 p-3 bg-green-50 border-l-2 border-green-200 rounded-r-md">
                    <div className="flex items-center space-x-1 mb-1">
                      <Bot className="w-3 h-3 text-green-600" />
                      <span className="text-xs font-medium text-green-700">Auto-Reply Sent</span>
                    </div>
                    <p className="text-xs text-green-600 italic">
                      "Thank you for your feedback! We appreciate your input..."
                    </p>
                  </div>
                )}

                {/* Escalation Notice */}
                {comment.escalated && (
                  <div className="mt-3 p-3 bg-yellow-50 border-l-2 border-yellow-200 rounded-r-md">
                    <div className="flex items-center space-x-1">
                      <AlertTriangle className="w-3 h-3 text-yellow-600" />
                      <span className="text-xs font-medium text-yellow-700">Escalated to Human Review</span>
                    </div>
                  </div>
                )}

                {/* Hidden Notice */}
                {comment.hidden && (
                  <div className="mt-3 p-3 bg-gray-50 border-l-2 border-gray-200 rounded-r-md">
                    <div className="flex items-center space-x-1">
                      <EyeOff className="w-3 h-3 text-gray-600" />
                      <span className="text-xs font-medium text-gray-700">Hidden from Public View</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};