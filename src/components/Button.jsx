import React from 'react';

/**
 * Reusable Button component with variants
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  onClick,
  disabled = false,
  className = '',
  type = 'button',
  as = 'button'
}) => {
  const Component = as;
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
    danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500'
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  const componentProps = Component === 'button'
    ? { type, onClick, disabled }
    : { onClick };

  return (
    <Component
      {...componentProps}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {icon && <span className="mr-2">{icon}</span>}
      {children}
    </Component>
  );
};
