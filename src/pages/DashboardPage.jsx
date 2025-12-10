import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  TrendingDown,
  TrendingUp,
  PiggyBank,
  Loader,
  ChevronDown,
  Calendar,
  Clock
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { dashboardAPI, transactionsAPI, recurringAPI, transformTransaction, formatCurrency } from '../services/api';

/**
 * Dashboard page component matching Lemonex reference design
 */
// Chart colors matching pie chart palette
const CHART_COLORS = ['#14b8a6', '#0d9488', '#f97316', '#8b5cf6', '#ea580c', '#ec4899', '#06b6d4', '#0f766e'];

// Get color by index (for category bars)
const getCategoryColor = (index) => {
  return CHART_COLORS[index % CHART_COLORS.length];
};

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [chartType, setChartType] = useState('income'); // 'income' or 'expenses'
  const [dateRange, setDateRange] = useState('last_30_days');
  const [dateDropdownOpen, setDateDropdownOpen] = useState(false);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [aggregates, setAggregates] = useState(null);
  const [upcomingPayments, setUpcomingPayments] = useState([]);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const dateDropdownRef = useRef(null);

  const dateRangeOptions = [
    { label: 'Last 7 days', value: 'last_7_days' },
    { label: 'Last 30 days', value: 'last_30_days' },
    { label: 'This Month', value: 'this_month' },
    { label: 'Last Month', value: 'last_month' },
    { label: 'Last 3 Months', value: 'last_3_months' }
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dateDropdownRef.current && !dateDropdownRef.current.contains(event.target)) {
        setDateDropdownOpen(false);
      }
    };

    if (dateDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [dateDropdownOpen]);

  // Fetch dashboard data on mount and when date range changes
  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        // Fetch all dashboard data in parallel
        const [statsResponse, transResponse, upcomingResponse, categoriesResponse] = await Promise.all([
          dashboardAPI.getStats(dateRange),
          transactionsAPI.getView({
            date_range: dateRange,
            page: 1,
            page_size: 20
          }),
          recurringAPI.getUpcoming(14),
          transactionsAPI.getCategories()
        ]);

        setDashboardStats(statsResponse.data);

        const transformedTransactions = transResponse.data.rows.map(transformTransaction);
        setTransactions(transformedTransactions);
        setAggregates(transResponse.data.aggregates);

        // Set upcoming payments
        setUpcomingPayments(upcomingResponse.data || []);

        // Process and set category breakdown (top 5 by total amount)
        const categories = categoriesResponse.data || [];
        const sortedCategories = categories
          .filter(cat => cat.category !== 'Income' && cat.total_amount < 0) // Only expenses
          .sort((a, b) => Math.abs(b.total_amount) - Math.abs(a.total_amount))
          .slice(0, 5);
        setCategoryBreakdown(sortedCategories);

      } catch (error) {
        // Error handled silently - dashboard shows empty state
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [dateRange]);

  const recentTransactions = transactions.slice(0, 5);

  // Process chart data
  const chartData = aggregates?.by_day?.map(day => {
    const [year, month, dayNum] = day.date.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(dayNum));
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      income: day.net > 0 ? day.net : 0,
      expenses: day.net < 0 ? Math.abs(day.net) : 0,
      sortDate: day.date
    };
  }).sort((a, b) => a.sortDate.localeCompare(b.sortDate)) || [];

  // Get savings rate from API
  const savingsRate = dashboardStats?.savings_rate || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader size={32} className="animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Content - 3 columns */}
        <div className="lg:col-span-3 space-y-6">
          {/* Metrics Container - Single card with 3 sections */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-gray-100">
              {/* Total Income */}
              <div className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center flex-shrink-0">
                  <TrendingUp size={22} />
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium">Total Income</p>
                  <p className="text-2xl font-bold text-gray-900 tracking-tight">{formatCurrency(dashboardStats?.total_income || 0)}</p>
                  <p className="text-xs text-gray-400 mt-0.5">This period</p>
                </div>
              </div>

              {/* Total Expenses */}
              <div className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center flex-shrink-0">
                  <TrendingDown size={22} />
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium">Total Expenses</p>
                  <p className="text-2xl font-bold text-gray-900 tracking-tight">{formatCurrency(Math.abs(dashboardStats?.total_expenses || 0))}</p>
                  <p className="text-xs text-gray-400 mt-0.5">This period</p>
                </div>
              </div>

              {/* Savings Rate */}
              <div className="p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-accent-50 text-accent-600 flex items-center justify-center flex-shrink-0">
                  <PiggyBank size={22} />
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium">Savings Rate</p>
                  <p className="text-2xl font-bold text-gray-900 tracking-tight">{savingsRate.toFixed(1)}%</p>
                  <div className={`flex items-center gap-1.5 text-sm mt-0.5 ${savingsRate >= 0 ? 'text-primary-600' : 'text-red-500'}`}>
                    <span className={`w-2 h-2 rounded-full ${savingsRate >= 0 ? 'bg-primary-500' : 'bg-red-500'}`} />
                    <span className="font-medium">{savingsRate >= 20 ? 'Healthy' : savingsRate >= 10 ? 'Good' : 'Needs work'}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Statistics Chart */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
              <div className="flex items-center gap-6">
                <h3 className="text-lg font-semibold text-gray-900">Statistics</h3>
                {/* Income/Expenses Toggle */}
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="chartType"
                      checked={chartType === 'income'}
                      onChange={() => setChartType('income')}
                      className="w-4 h-4 text-primary-500 border-gray-300 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-600">Income</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="chartType"
                      checked={chartType === 'expenses'}
                      onChange={() => setChartType('expenses')}
                      className="w-4 h-4 text-primary-500 border-gray-300 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-600">Expenses</span>
                  </label>
                </div>
              </div>

              {/* Date Range Dropdown */}
              <div className="relative" ref={dateDropdownRef}>
                <button
                  onClick={() => setDateDropdownOpen(!dateDropdownOpen)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {dateRangeOptions.find(opt => opt.value === dateRange)?.label}
                  <ChevronDown size={16} className={`transition-transform ${dateDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {dateDropdownOpen && (
                  <div className="absolute z-50 mt-1 right-0 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                    {dateRangeOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => {
                          setDateRange(option.value);
                          setDateDropdownOpen(false);
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors ${
                          option.value === dateRange ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Area Chart */}
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.05}/>
                  </linearGradient>
                  <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0.05}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(value) => `${value / 1000}K`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                  formatter={(value) => [`$${value.toFixed(2)}`, chartType === 'income' ? 'Income' : 'Expenses']}
                />
                {chartType === 'income' ? (
                  <Area
                    type="monotone"
                    dataKey="income"
                    stroke="#14b8a6"
                    strokeWidth={2}
                    fill="url(#colorIncome)"
                  />
                ) : (
                  <Area
                    type="monotone"
                    dataKey="expenses"
                    stroke="#f97316"
                    strokeWidth={2}
                    fill="url(#colorExpenses)"
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Recent Transactions */}
          <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Recent Transaction</h3>
              <button
                onClick={() => navigate('/transactions')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                View All &gt;
              </button>
            </div>

            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Name / Business</th>
                    <th className="text-left py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Type</th>
                    <th className="text-left py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Amount</th>
                    <th className="text-left py-3 text-xs font-medium text-gray-400 uppercase tracking-wider">Date</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {recentTransactions.map((transaction) => (
                    <tr key={transaction.id} className="border-b border-gray-50">
                      <td className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600 font-medium text-sm">
                            {transaction.merchant.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{transaction.merchant}</p>
                            <p className="text-xs text-gray-500">{transaction.category}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 text-sm text-gray-600">{transaction.category}</td>
                      <td className="py-4 text-sm font-medium text-gray-900">
                        ${Math.abs(transaction.amount).toFixed(2)}
                      </td>
                      <td className="py-4 text-sm text-gray-500">
                        {(() => {
                          const [year, month, day] = transaction.date.split('-');
                          const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                          return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
                        })()}
                      </td>
                      
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="md:hidden space-y-3">
              {recentTransactions.map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600 font-medium">
                      {transaction.merchant.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{transaction.merchant}</p>
                      <p className="text-xs text-gray-500">{transaction.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">${Math.abs(transaction.amount).toFixed(2)}</p>
                    <p className="text-xs text-gray-500">
                      {(() => {
                        const [year, month, day] = transaction.date.split('-');
                        const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                        return date.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                      })()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Sidebar - 1 column */}
        <div className="space-y-6">
          {/* Credit Card */}
          <div className="bg-gradient-to-br from-primary-700 via-primary-800 to-primary-900 rounded-xl p-5 text-white">
            <div className="flex justify-between items-start mb-8">
              <span className="text-xs text-gray-400">VISA</span>
              <span className="font-bold tracking-wider">••••••••2345</span>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-gray-400 mb-1">Card Holder name</p>
                <p className="text-sm font-medium">{user?.name || user?.email || 'User'}</p>
              </div>
              <div className="flex justify-between">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Expiry Date</p>
                  <p className="text-sm font-medium">02/30</p>
                </div>
              </div>
            </div>
          </div>

          {/* Upcoming Payments */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-gray-900">Upcoming Payments</h3>
              <button
                onClick={() => navigate('/recurring')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                View All &gt;
              </button>
            </div>

            {upcomingPayments.length > 0 ? (
              <div className="space-y-4">
                {upcomingPayments.slice(0, 4).map((payment, index) => {
                  const color = getCategoryColor(index);
                  return (
                    <div key={payment.merchant_key || index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-medium text-white"
                          style={{ backgroundColor: color }}
                        >
                          {payment.merchant_name?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{payment.merchant_name}</p>
                          <p className="text-xs text-gray-500 flex items-center gap-1">
                            <Clock size={12} />
                            in {payment.days_until} day{payment.days_until !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      <span className="text-sm font-medium text-accent-500">
                        -{formatCurrency(Math.abs(payment.amount))}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6">
                <Calendar size={32} className="mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-500">No upcoming payments</p>
              </div>
            )}
          </div>

          {/* Category Breakdown */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-gray-900">Top Expenses</h3>
              <button
                onClick={() => navigate('/transactions')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                View All &gt;
              </button>
            </div>

            {categoryBreakdown.length > 0 ? (
              <div className="space-y-3">
                {(() => {
                  const maxAmount = Math.max(...categoryBreakdown.map(c => Math.abs(c.total_amount)));
                  return categoryBreakdown.map((cat, index) => {
                    const color = getCategoryColor(index);
                    const absAmount = Math.abs(cat.total_amount);
                    const percentage = (absAmount / maxAmount) * 100;
                    return (
                      <div key={cat.category}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-sm text-gray-700">{cat.category}</span>
                          </div>
                          <span className="text-sm font-medium text-gray-900">{formatCurrency(absAmount)}</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{ width: `${percentage}%`, backgroundColor: color }}
                          />
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            ) : (
              <div className="text-center py-6">
                <PiggyBank size={32} className="mx-auto text-gray-300 mb-2" />
                <p className="text-sm text-gray-500">No spending data yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
