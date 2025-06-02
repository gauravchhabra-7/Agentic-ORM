import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { FilterSidebar } from './FilterSidebar';
import type { Client, FilterOptions } from '../../types';

interface MainLayoutProps {
  children: React.ReactNode;
  clients: Client[];
  selectedClient: Client | null;
  onClientChange: (client: Client) => void;
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  clients,
  selectedClient,
  onClientChange,
  filters,
  onFiltersChange,
}) => {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation */}
        <TopNavbar
          clients={clients}
          selectedClient={selectedClient}
          onClientChange={onClientChange}
          showFilters={showFilters}
          onToggleFilters={() => setShowFilters(!showFilters)}
        />

        {/* Main Content with Optional Filter Sidebar */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Dashboard Content */}
          <main className="flex-1 overflow-auto">
            <div className="p-6">
              {children}
            </div>
          </main>

          {/* Right Filter Sidebar */}
          {showFilters && (
            <div className="w-80 border-l border-gray-200 bg-white">
              <FilterSidebar
                filters={filters}
                onFiltersChange={onFiltersChange}
                onClose={() => setShowFilters(false)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};