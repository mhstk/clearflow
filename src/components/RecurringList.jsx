import React from 'react';
import { Badge, getCategoryBadgeVariant } from './Badge';

/**
 * RecurringList component for displaying recurring payments
 */
export const RecurringList = ({ recurringPayments, loading = false }) => {
  const formatAmount = (amount) => {
    return `$${Math.abs(amount).toFixed(2)}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getFrequencyBadgeVariant = (frequency) => {
    const variants = {
      'monthly': 'info',
      'weekly': 'success',
      'yearly': 'warning',
      'quarterly': 'purple',
      'bi-weekly': 'info'
    };
    return variants[frequency?.toLowerCase()] || 'default';
  };

  const formatFrequency = (frequency) => {
    if (!frequency) return 'Unknown';
    return frequency.charAt(0).toUpperCase() + frequency.slice(1);
  };

  const getConfidenceBadge = (confidence) => {
    const variants = {
      'high': 'success',
      'medium': 'warning',
      'low': 'default'
    };
    return variants[confidence?.toLowerCase()] || 'default';
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!recurringPayments || recurringPayments.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No recurring payments detected yet.</p>
        <p className="text-sm text-gray-400 mt-2">
          Click "Analyze Subscriptions" to detect recurring payments from your transactions.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {recurringPayments.map((payment, index) => (
        <div
          key={payment.merchant_key || index}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {payment.merchant_name || payment.merchant_key}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {payment.next_expected_date ? (
                  <>Next charge: {formatDate(payment.next_expected_date)}</>
                ) : (
                  <>Last: {formatDate(payment.last_transaction_date)}</>
                )}
              </p>
            </div>
            {payment.confidence && (
              <Badge variant={getConfidenceBadge(payment.confidence)} size="sm">
                {payment.confidence}
              </Badge>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Amount</span>
              <span className="text-lg font-semibold text-gray-900">
                {formatAmount(payment.typical_amount)}
                {payment.amount_variance === 'variable' && (
                  <span className="text-xs text-gray-500 ml-1">~</span>
                )}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Frequency</span>
              <Badge variant={getFrequencyBadgeVariant(payment.frequency)}>
                {formatFrequency(payment.frequency)}
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Category</span>
              <Badge variant={getCategoryBadgeVariant(payment.category)}>
                {payment.category}
              </Badge>
            </div>

            {payment.transaction_count && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Occurrences</span>
                <span className="text-sm text-gray-900">{payment.transaction_count}x</span>
              </div>
            )}

            {payment.ai_notes && (
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-500">{payment.ai_notes}</p>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
