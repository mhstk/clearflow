import React from 'react';

/**
 * Placeholder page for routes under development
 */
export const PlaceholderPage = ({ title, description }) => {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-4xl">🚧</span>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
        <p className="text-gray-500">{description}</p>
      </div>
    </div>
  );
};
