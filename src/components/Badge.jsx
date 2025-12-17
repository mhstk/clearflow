import React from 'react';

/**
 * Badge component for categories, statuses, etc.
 * Supports both preset variants and custom colors.
 */
export const Badge = ({ children, variant = 'default', size = 'md', color = null }) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    default: 'bg-gray-100 text-gray-700',
    primary: 'bg-primary-100 text-primary-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
    purple: 'bg-purple-100 text-purple-700',
    pink: 'bg-pink-100 text-pink-700',
    orange: 'bg-orange-100 text-orange-700',
    cyan: 'bg-cyan-100 text-cyan-700'
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-sm',
    lg: 'px-3 py-1 text-base'
  };

  // If custom color is provided, use it with appropriate opacity
  if (color) {
    return (
      <span
        className={`${baseStyles} ${sizes[size]}`}
        style={{
          backgroundColor: `${color}20`, // 20% opacity
          color: color
        }}
      >
        {children}
      </span>
    );
  }

  return (
    <span className={`${baseStyles} ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  );
};

/**
 * Get badge variant based on category
 */
export const getCategoryBadgeVariant = (category) => {
  const categoryColors = {
    'Groceries': 'success',
    'Dining': 'info',
    'Transportation': 'warning',
    'Entertainment': 'pink',
    'Shopping': 'purple',
    'Health': 'cyan',
    'Utilities': 'danger',
    'Subscriptions': 'primary',
    'Income': 'success',
    'Cash': 'default'
  };

  return categoryColors[category] || 'default';
};
