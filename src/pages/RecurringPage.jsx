import React, { useState, useEffect, useCallback } from 'react';
import { RecurringList } from '../components/RecurringList';
import { ChartCard } from '../components/ChartCard';
import { Button } from '../components/Button';
import { Sparkles, RefreshCw, AlertCircle, TrendingUp, Calendar } from 'lucide-react';
import { recurringAPI } from '../services/api';

/**
 * Recurring payments page with AI-powered detection and insights
 */
export const RecurringPage = () => {
  const [recurringPayments, setRecurringPayments] = useState([]);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalCount: 0,
    totalMonthly: 0,
    totalYearly: 0
  });

  // Fetch recurring payments
  const fetchRecurringPayments = useCallback(async (forceRefresh = false) => {
    try {
      setError(null);
      if (!forceRefresh) setLoading(true);

      const response = await recurringAPI.getRecurringPayments(forceRefresh);
      const data = response.data;

      setRecurringPayments(data.recurring_payments || []);
      setStats({
        totalCount: data.total_count || 0,
        totalMonthly: data.total_monthly || 0,
        totalYearly: data.total_yearly || 0
      });
    } catch (err) {
      setError('Failed to load recurring payments');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch insights
  const fetchInsights = useCallback(async () => {
    try {
      const response = await recurringAPI.getInsights();
      setInsights(response.data);
    } catch (err) {
      // Insights are optional, don't show error
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchRecurringPayments();
    fetchInsights();
  }, [fetchRecurringPayments, fetchInsights]);

  // Handle analyze button - triggers fresh AI analysis
  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);
      setError(null);

      // Trigger background recurring detection
      await recurringAPI.analyzeRecurring();

      // Wait a bit for detection to complete
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Fetch updated recurring payments
      await fetchRecurringPayments(true);

      // Force regenerate insights (saves to DB)
      const insightsResponse = await recurringAPI.getInsights(true);
      setInsights(insightsResponse.data);

    } catch (err) {
      setError('Failed to analyze recurring payments');
    } finally {
      setAnalyzing(false);
    }
  };

  // Get insight icon and color
  const getInsightStyle = (type, priority) => {
    if (priority === 'warning') {
      return {
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        iconBg: 'bg-red-100',
        iconColor: 'text-red-600',
        Icon: AlertCircle
      };
    }
    if (type === 'optimization') {
      return {
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        iconBg: 'bg-green-100',
        iconColor: 'text-green-600',
        Icon: TrendingUp
      };
    }
    if (type === 'prediction') {
      return {
        bgColor: 'bg-purple-50',
        borderColor: 'border-purple-200',
        iconBg: 'bg-purple-100',
        iconColor: 'text-purple-600',
        Icon: Calendar
      };
    }
    // Default: cost_analysis, info
    return {
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      Icon: Sparkles
    };
  };

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="text-red-600 mr-3" size={20} />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-600 mb-1">Total Recurring</p>
          <p className="text-3xl font-bold text-gray-900">
            {loading ? '-' : stats.totalCount}
          </p>
          <p className="text-sm text-gray-500 mt-2">Detected subscriptions</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-600 mb-1">Monthly Total</p>
          <p className="text-3xl font-bold text-gray-900">
            {loading ? '-' : `$${stats.totalMonthly.toFixed(2)}`}
          </p>
          <p className="text-sm text-gray-500 mt-2">Recurring monthly charges</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <p className="text-sm font-medium text-gray-600 mb-1">Annual Total</p>
          <p className="text-3xl font-bold text-gray-900">
            {loading ? '-' : `$${stats.totalYearly.toFixed(2)}`}
          </p>
          <p className="text-sm text-gray-500 mt-2">Estimated yearly cost</p>
        </div>
      </div>

      {/* AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartCard
            title="Recurring Payment Insights"
            subtitle="AI-powered analysis of your subscriptions"
          >
            <div className="space-y-4">
              {insights?.insights && insights.insights.length > 0 ? (
                insights.insights.map((insight, index) => {
                  const style = getInsightStyle(insight.type, insight.priority);
                  return (
                    <div
                      key={index}
                      className={`flex items-start p-4 ${style.bgColor} rounded-lg border ${style.borderColor}`}
                    >
                      <div className={`flex-shrink-0 w-8 h-8 ${style.iconBg} rounded-full flex items-center justify-center mr-3`}>
                        <style.Icon size={16} className={style.iconColor} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{insight.title}</p>
                        <p className="text-sm text-gray-700 mt-1">{insight.message}</p>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                    <Sparkles size={16} className="text-gray-600" />
                  </div>
                  <p className="text-sm text-gray-700">
                    {loading
                      ? 'Loading insights...'
                      : 'Click "Analyze Subscriptions" to generate AI insights about your recurring payments.'}
                  </p>
                </div>
              )}

              {/* Category Breakdown */}
              {insights?.summary?.by_category && Object.keys(insights.summary.by_category).length > 0 && (
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-3">Spending by Category</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(insights.summary.by_category).map(([category, amount]) => (
                      <div key={category} className="flex justify-between items-center bg-gray-50 rounded-lg px-3 py-2">
                        <span className="text-sm text-gray-600">{category}</span>
                        <span className="text-sm font-medium text-gray-900">${amount.toFixed(2)}/mo</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ChartCard>
        </div>

        <div>
          <ChartCard title="Quick Actions">
            <Button
              variant="primary"
              className="w-full"
              icon={analyzing ? <RefreshCw size={18} className="animate-spin" /> : <Sparkles size={18} />}
              onClick={handleAnalyze}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing...' : 'Analyze Subscriptions'}
            </Button>

            {/* Upcoming Payments */}
            {insights?.upcoming && insights.upcoming.length > 0 && (
              <div className="mt-6 pt-4 border-t border-gray-200">
                <p className="text-sm font-medium text-gray-700 mb-3">Upcoming Payments</p>
                <div className="space-y-2">
                  {insights.upcoming.slice(0, 3).map((payment, index) => (
                    <div key={index} className="flex justify-between items-center bg-gray-50 rounded-lg px-3 py-2">
                      <div>
                        <p className="text-sm font-medium text-gray-900 truncate" style={{ maxWidth: '120px' }}>
                          {payment.merchant_name || payment.merchant}
                        </p>
                        <p className="text-xs text-gray-500">
                          in {payment.days_until} day{payment.days_until !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <span className="text-sm font-medium text-gray-900">${payment.amount.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ChartCard>
        </div>
      </div>

      {/* Recurring Payments List */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Recurring Payments</h3>
        <RecurringList recurringPayments={recurringPayments} loading={loading} />
      </div>
    </div>
  );
};
