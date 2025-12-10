import React from 'react';

/**
 * ChartCard component - wrapper for charts with title and actions
 */
export const ChartCard = ({ title, subtitle, children, actions, className = '' }) => {
  return (
    <div className={`bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-6 ${className}`}>
      <div className="flex items-start sm:items-center justify-between mb-4 sm:mb-6">
        <div className="min-w-0 flex-1">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">{title}</h3>
          {subtitle && <p className="text-xs sm:text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {actions && (
          <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
            {actions}
          </div>
        )}
      </div>
      <div className="w-full">
        {children}
      </div>
    </div>
  );
};
