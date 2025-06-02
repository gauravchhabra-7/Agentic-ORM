import React from 'react';
import { 
  BarChart3, 
  MessageCircle, 
  TrendingUp, 
  Shield, 
  AlertTriangle,
  Zap,
  Settings,
  Bot,
  Eye,
  MessageSquare,
  Activity,
  FileText,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  activeSection?: string;
  onSectionChange?: (section: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  badge?: string | number;
  children?: NavItem[];
}

const navigationItems: NavItem[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: BarChart3,
  },
  {
    id: 'monitor',
    label: 'MONITOR',
    icon: Eye,
    children: [
      { id: 'comment-stream', label: 'Comment Stream', icon: MessageCircle, badge: '12' },
      { id: 'sentiment', label: 'Sentiment Analysis', icon: TrendingUp },
      { id: 'toxicity', label: 'Toxicity Detection', icon: Shield, badge: '3' },
      { id: 'escalation', label: 'Escalation Queue', icon: AlertTriangle, badge: '5' },
    ]
  },
  {
    id: 'automate',
    label: 'AUTOMATE',
    icon: Bot,
    children: [
      { id: 'auto-replies', label: 'Auto-Replies', icon: MessageSquare },
      { id: 'moderation', label: 'Content Moderation', icon: Shield },
      { id: 'rules', label: 'Business Rules', icon: Settings },
      { id: 'history', label: 'Action History', icon: Activity },
    ]
  },
  {
    id: 'analytics',
    label: 'ANALYTICS',
    icon: BarChart3,
    children: [
      { id: 'performance', label: 'Performance Metrics', icon: TrendingUp },
      { id: 'effectiveness', label: 'Response Effectiveness', icon: Zap },
      { id: 'reports', label: 'Client Reports', icon: FileText },
    ]
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeSection = 'overview', 
  onSectionChange 
}) => {
  const [expandedSections, setExpandedSections] = React.useState<string[]>(['monitor']);

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => 
      prev.includes(sectionId) 
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const handleItemClick = (itemId: string, hasChildren: boolean) => {
    if (hasChildren) {
      toggleSection(itemId);
    } else {
      onSectionChange?.(itemId);
    }
  };

  const renderNavItem = (item: NavItem, level: number = 0) => {
    const isActive = activeSection === item.id;
    const isExpanded = expandedSections.includes(item.id);
    const hasChildren = !!(item.children && item.children.length > 0);
    const Icon = item.icon;

    return (
      <div key={item.id}>
        <button
          onClick={() => handleItemClick(item.id, hasChildren)}
          className={`
            w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150
            ${level === 0 ? 'mt-2' : 'mt-1 ml-4'}
            ${isActive 
              ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-500' 
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            }
          `}
        >
          <div className="flex items-center">
            <Icon className={`w-4 h-4 mr-3 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
            <span className={`${level === 0 && hasChildren ? 'text-xs font-semibold tracking-wider uppercase' : ''}`}>
              {item.label}
            </span>
            {item.badge && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                {item.badge}
              </span>
            )}
          </div>
          {hasChildren && (
            <ChevronRight 
              className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`} 
            />
          )}
        </button>

        {/* Render children if expanded */}
        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderNavItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo/Brand */}
      <div className="flex items-center px-6 py-4 border-b border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <h1 className="text-lg font-semibold text-gray-900">ORM-MVP</h1>
            <p className="text-xs text-gray-500">Agentic Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {navigationItems.map(item => renderNavItem(item))}
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-gray-200 p-4">
        <div className="bg-primary-50 rounded-lg p-3">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Zap className="w-5 h-5 text-primary-600" />
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-primary-800">
                Automation Rate
              </p>
              <p className="text-xs text-primary-600">
                95.1% efficiency
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};