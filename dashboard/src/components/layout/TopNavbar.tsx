import React, { useState } from 'react';
import { 
  Filter, 
  Search, 
  Bell, 
  Settings, 
  User, 
  ChevronDown,
  Download,
  RefreshCw,
  Activity
} from 'lucide-react';
import type { Client } from '../../types';

interface TopNavbarProps {
  clients: Client[];
  selectedClient: Client | null;
  onClientChange: (client: Client) => void;
  showFilters: boolean;
  onToggleFilters: () => void;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({
  clients,
  selectedClient,
  onClientChange,
  showFilters,
  onToggleFilters,
}) => {
  const [showClientDropdown, setShowClientDropdown] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const getStatusColor = (status: 'active' | 'inactive') => {
    return status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  const getPlanBadgeColor = (plan: 'basic' | 'pro' | 'enterprise') => {
    switch (plan) {
      case 'basic': return 'bg-blue-100 text-blue-800';
      case 'pro': return 'bg-purple-100 text-purple-800';
      case 'enterprise': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left Section - Client Selector & Actions */}
        <div className="flex items-center space-x-4">
          {/* Client Selector */}
          <div className="relative">
            <button
              onClick={() => setShowClientDropdown(!showClientDropdown)}
              className="flex items-center space-x-3 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-150"
            >
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${selectedClient?.status === 'active' ? 'bg-green-400' : 'bg-gray-400'}`} />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {selectedClient?.name || 'Select Client'}
                  </p>
                  {selectedClient && (
                    <p className="text-xs text-gray-500 capitalize">
                      {selectedClient.plan} plan
                    </p>
                  )}
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* Client Dropdown */}
            {showClientDropdown && (
              <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="p-2">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 py-2">
                    Select Client
                  </div>
                  {clients.map(client => (
                    <button
                      key={client.id}
                      onClick={() => {
                        onClientChange(client);
                        setShowClientDropdown(false);
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-50 rounded-md"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${client.status === 'active' ? 'bg-green-400' : 'bg-gray-400'}`} />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{client.name}</p>
                          <div className="flex items-center space-x-2">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(client.status)}`}>
                              {client.status}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${getPlanBadgeColor(client.plan)}`}>
                              {client.plan}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors duration-150">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors duration-150">
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="flex-1 max-w-md mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search comments, users, or actions..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Right Section - Filters & User Menu */}
        <div className="flex items-center space-x-4">
          {/* System Status */}
          <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-full">
            <Activity className="w-3 h-3 text-green-600" />
            <span className="text-xs font-medium text-green-700">System Active</span>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={onToggleFilters}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors duration-150 ${
              showFilters 
                ? 'bg-primary-100 text-primary-700' 
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">Filters</span>
          </button>

          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors duration-150">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-md transition-colors duration-150"
            >
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute top-full right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="p-2">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">Demo User</p>
                    <p className="text-xs text-gray-500">admin@orm-mvp.com</p>
                  </div>
                  <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-gray-50 rounded-md">
                    <Settings className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-700">Settings</span>
                  </button>
                  <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-gray-50 rounded-md">
                    <User className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-700">Profile</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Click outside handlers */}
      {(showClientDropdown || showUserMenu) && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => {
            setShowClientDropdown(false);
            setShowUserMenu(false);
          }}
        />
      )}
    </header>
  );
};