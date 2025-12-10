import React from 'react';

/**
 * MetricCard component matching Lemonex reference design
 */
export const MetricCard = ({
  icon,
  iconBgColor = 'bg-primary-50',
  iconColor = 'text-primary-600',
  label,
  value,
  percentChange = 0
}) => {
  const isPositive = percentChange >= 0;

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
      <div className="flex items-center gap-4">
        {/* Icon Circle */}
        <div className={`w-12 h-12 rounded-full ${iconBgColor} ${iconColor} flex items-center justify-center flex-shrink-0`}>
          {icon}
        </div>

        {/* Content */}
        <div className="min-w-0">
          <p className="text-sm text-gray-500 mb-0.5">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {percentChange !== undefined && (
            <div className={`flex items-center gap-1.5 text-sm mt-1 ${isPositive ? 'text-primary-600' : 'text-accent-500'}`}>
              <span className={`w-2 h-2 rounded-full ${isPositive ? 'bg-primary-500' : 'bg-accent-500'}`} />
              <span className="font-medium">{isPositive ? '+' : ''}{percentChange.toFixed(2)}%</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
