import React, { useState, useEffect } from 'react';
import { TransactionsTable } from '../components/TransactionsTable';
import { ChartCard } from '../components/ChartCard';
import { Loader, Download } from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Sector,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { transactionsAPI, aiAPI, transformTransaction } from '../services/api';

/**
 * Transactions page with filtering and Excel-like behavior
 */
export const TransactionsPage = ({ filters: propFilters, categories: propCategories }) => {
  // Default filters if not provided via props
  const defaultFilters = {
    dateRange: 'this_month',
    startDate: '',
    endDate: '',
    transactionType: 'all',
    categories: [],
    merchant: '',
    amountMin: '',
    amountMax: ''
  };

  const filters = propFilters || defaultFilters;

  const [transactions, setTransactions] = useState([]);
  const [aggregates, setAggregates] = useState(null);
  const [localCategories, setLocalCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePieIndex, setActivePieIndex] = useState(null);

  const categories = propCategories || localCategories;

  // Fetch categories on mount (only if not provided via props)
  useEffect(() => {
    if (propCategories) return;

    const fetchCategories = async () => {
      try {
        const response = await aiAPI.getCategories();
        setLocalCategories(response.data);
      } catch (err) {
        // Set default categories if API fails
        setLocalCategories(['Groceries', 'Rent', 'Transport', 'Eating Out', 'Shopping', 'Subscription', 'Utilities', 'Income', 'Other', 'Uncategorized']);
      }
    };

    fetchCategories();
  }, [propCategories]);

  // Fetch transactions when filters change
  useEffect(() => {
    const fetchTransactions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const params = {
          page: 1,
          page_size: 1000, // Get all transactions for now
        };

        // Handle date range - custom dates override predefined range
        if (filters.startDate || filters.endDate) {
          // Use custom dates if provided
          if (filters.startDate) params.start_date = filters.startDate;
          if (filters.endDate) params.end_date = filters.endDate;
        } else {
          // Use predefined date range
          params.date_range = filters.dateRange;
        }

        // Add optional filters
        if (filters.categories.length > 0) {
          params.category = filters.categories;
        }
        if (filters.merchant) {
          params.merchant_query = filters.merchant;
        }

        // Handle amount filtering based on transaction type
        const transactionType = filters.transactionType || 'all';

        if (filters.amountMin || filters.amountMax) {
          const minAmount = filters.amountMin ? parseFloat(filters.amountMin) : 0;
          const maxAmount = filters.amountMax ? parseFloat(filters.amountMax) : Infinity;

          if (transactionType === 'expenses') {
            // For expenses (negative amounts), convert positive inputs to negative range
            // User enters 50-100, we want -100 to -50
            if (filters.amountMax) params.min_amount = -maxAmount;
            if (filters.amountMin) params.max_amount = -minAmount;
          } else if (transactionType === 'income') {
            // For income (positive amounts), use positive range as-is
            if (filters.amountMin) params.min_amount = minAmount;
            if (filters.amountMax) params.max_amount = maxAmount;
          } else {
            // For 'all', filter by absolute value on frontend after fetching
            // We'll fetch all and filter client-side
          }
        }

        const response = await transactionsAPI.getView(params);
        const data = response.data;

        // Transform transactions to frontend format
        let transformedTransactions = data.rows.map(transformTransaction);

        // Client-side filtering for transaction type and amount when type is 'all'
        transformedTransactions = transformedTransactions.filter(t => {
          // Filter by transaction type
          if (transactionType === 'expenses' && t.amount >= 0) return false;
          if (transactionType === 'income' && t.amount < 0) return false;

          // Filter by amount range when transaction type is 'all'
          if (transactionType === 'all' && (filters.amountMin || filters.amountMax)) {
            const absAmount = Math.abs(t.amount);
            const minAmount = filters.amountMin ? parseFloat(filters.amountMin) : 0;
            const maxAmount = filters.amountMax ? parseFloat(filters.amountMax) : Infinity;

            if (absAmount < minAmount || absAmount > maxAmount) return false;
          }

          return true;
        });

        setTransactions(transformedTransactions);
        setAggregates(data.aggregates);

      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load transactions');
        setTransactions([]);
        setAggregates(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTransactions();
  }, [filters]);

  const handleCategoryUpdate = async (transactionId, newCategory) => {
    try {
      // Call API to update category
      await transactionsAPI.updateCategory(transactionId, newCategory);

      // Update local state optimistically
      setTransactions(prevTransactions =>
        prevTransactions.map(t =>
          t.id === transactionId ? { ...t, category: newCategory } : t
        )
      );

      // Optionally refetch aggregates to update charts
      const params = {
        date_range: filters.dateRange,
        page: 1,
        page_size: 1000,
      };
      if (filters.categories.length > 0) params.category = filters.categories;
      if (filters.merchant) params.merchant_query = filters.merchant;
      if (filters.amountMin) params.min_amount = parseFloat(filters.amountMin);
      if (filters.amountMax) params.max_amount = parseFloat(filters.amountMax);

      const response = await transactionsAPI.getView(params);
      setAggregates(response.data.aggregates);
    } catch (err) {
      setError('Failed to update category');
    }
  };

  const handleTransactionUpdate = async (transactionId, updates) => {
    try {
      // Call API to update note if provided
      if (updates.noteUser !== undefined) {
        await transactionsAPI.updateNote(transactionId, updates.noteUser);
      }

      // Call API to update date/amount if provided
      if (updates.date !== undefined || updates.amount !== undefined) {
        await transactionsAPI.updateTransaction(transactionId, {
          ...(updates.date !== undefined && { date: updates.date }),
          ...(updates.amount !== undefined && { amount: updates.amount })
        });
      }

      // Update local state optimistically
      setTransactions(prevTransactions =>
        prevTransactions.map(t =>
          t.id === transactionId ? { ...t, ...updates } : t
        )
      );

      // Refetch aggregates if amount or date changed (affects charts)
      if (updates.date !== undefined || updates.amount !== undefined) {
        const params = {
          date_range: filters.dateRange,
          page: 1,
          page_size: 1000,
        };
        if (filters.categories.length > 0) params.category = filters.categories;
        if (filters.merchant) params.merchant_query = filters.merchant;
        if (filters.amountMin) params.min_amount = parseFloat(filters.amountMin);
        if (filters.amountMax) params.max_amount = parseFloat(filters.amountMax);

        const response = await transactionsAPI.getView(params);
        setAggregates(response.data.aggregates);
      }
    } catch (err) {
      setError('Failed to update transaction');
    }
  };

  const handleExportCSV = () => {
    if (transactions.length === 0) {
      alert('No transactions to export');
      return;
    }

    // Helper function to format date without timezone issues
    const formatDateForCSV = (dateString) => {
      // Parse YYYY-MM-DD format directly without timezone conversion
      const [year, month, day] = dateString.split('-');
      return `${month}/${day}/${year}`;
    };

    // CSV headers
    const headers = ['Date', 'Merchant', 'Category', 'Amount', 'Note', 'Description'];

    // Convert transactions to CSV rows
    const rows = transactions.map(t => [
      formatDateForCSV(t.date),
      t.merchant,
      t.category,
      t.amount.toFixed(2),
      t.noteUser || '',
      t.descriptionRaw
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => {
        // Escape cells containing commas, quotes, or newlines
        const cellStr = String(cell);
        if (cellStr.includes(',') || cellStr.includes('"') || cellStr.includes('\n')) {
          return `"${cellStr.replace(/"/g, '""')}"`;
        }
        return cellStr;
      }).join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    const dateRange = filters.dateRange.replace(/_/g, '-');
    const filename = `transactions-${dateRange}-${new Date().toISOString().split('T')[0]}.csv`;

    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Process aggregates for charts (expenses only, exclude income)
  const categoryBreakdown = aggregates?.by_category
    ? Object.entries(aggregates.by_category)
        .filter(([name, value]) => name !== 'Income' && value < 0) // Only expenses
        .map(([name, value], index) => {
          const colors = ['#14b8a6', '#0d9488', '#f97316', '#8b5cf6', '#ea580c', '#ec4899', '#06b6d4', '#0f766e'];
          return {
            name,
            value: Math.abs(value),
            color: colors[index % colors.length]
          };
        })
    : [];

  const dailySpending = aggregates?.by_day
    ? aggregates.by_day
        .filter(day => day.net < 0) // Only days with expenses
        .map(day => {
          // Parse YYYY-MM-DD format without timezone issues
          const [year, month, dayNum] = day.date.split('-');
          const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(dayNum));
          return {
            date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            amount: Math.abs(day.net),
            sortDate: day.date // Keep original date for sorting
          };
        })
        .sort((a, b) => a.sortDate.localeCompare(b.sortDate)) // Sort chronologically (oldest to newest)
    : [];

  const totalSpending = aggregates?.total_spent || 0;

  return (
    <div>
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Transactions</h2>
          <button
            onClick={handleExportCSV}
            disabled={transactions.length === 0}
            className="flex items-center justify-center text-sm text-primary-600 hover:text-primary-700 px-4 py-2 bg-primary-50 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={16} className="mr-2" />
            Export CSV
          </button>
        </div>
        {isLoading ? (
          <p className="text-xs sm:text-sm text-gray-500 flex items-center">
            <Loader size={14} className="mr-2 animate-spin" />
            Loading transactions...
          </p>
        ) : error ? (
          <p className="text-xs sm:text-sm text-red-600">{error}</p>
        ) : (
          <p className="text-xs sm:text-sm text-gray-500">
            Showing {transactions.length} transactions • Total Spent: $
            {Math.abs(totalSpending).toFixed(2)}
          </p>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Charts and Category Summary - 3 column grid: Category Table (left), Pie Chart (middle), Bar Chart (right) */}
      {!isLoading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
            {/* 1. Category Summary Table - LEFT */}
            {aggregates?.by_category && (() => {
              const expenseCategories = Object.entries(aggregates.by_category).filter(([_, amount]) => amount < 0);
              if (expenseCategories.length === 0) return null;

              const totalExpenses = expenseCategories.reduce((sum, [_, amount]) => sum + Math.abs(amount), 0);

              return (
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
                  <div className="p-4 border-b border-gray-100">
                    <h3 className="text-base font-semibold text-gray-900">Expenses by Category</h3>
                    <p className="text-xs text-gray-500 mt-0.5">Breakdown in selected range</p>
                  </div>
                  <div className="overflow-y-auto flex-1 max-h-[260px]">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                            Category
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                            Amount
                          </th>
                          <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                            %
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {expenseCategories
                          .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                          .map(([category, amount]) => {
                            const percentage = totalExpenses > 0 ? (Math.abs(amount) / totalExpenses) * 100 : 0;
                            return (
                              <tr key={category} className="hover:bg-gray-50 transition-colors">
                                <td className="px-3 py-2 whitespace-nowrap font-medium text-gray-900">
                                  {category}
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap font-semibold text-right text-red-600">
                                  ${Math.abs(amount).toFixed(2)}
                                </td>
                                <td className="px-3 py-2 whitespace-nowrap text-gray-600 text-right">
                                  {percentage.toFixed(1)}%
                                </td>
                              </tr>
                            );
                          })}
                      </tbody>
                    </table>
                  </div>
                  <div className="bg-gray-50 border-t border-gray-200 px-3 py-2">
                    <div className="flex justify-between text-sm font-bold">
                      <span className="text-gray-900">Total</span>
                      <span className="text-red-600">${totalExpenses.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* 2. Spending by Category Pie Chart - MIDDLE */}
            {categoryBreakdown.length > 0 && (
              <ChartCard title="Spending by Category" subtitle="Distribution of expenses">
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart onMouseLeave={() => setActivePieIndex(null)}>
                      <Pie
                        data={categoryBreakdown}
                        cx="50%"
                        cy="50%"
                        outerRadius={85}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ cx, cy, midAngle, outerRadius, name, percent, index }) => {
                          const RADIAN = Math.PI / 180;
                          const radius = outerRadius + 25;
                          const x = cx + radius * Math.cos(-midAngle * RADIAN);
                          const y = cy + radius * Math.sin(-midAngle * RADIAN);
                          const isActive = index === activePieIndex;

                          return (
                            <text
                              x={x}
                              y={y}
                              textAnchor={x > cx ? 'start' : 'end'}
                              dominantBaseline="central"
                              style={{
                                fontSize: isActive ? '16px' : '12px',
                                fontWeight: isActive ? 600 : 400,
                                fill: '#374151',
                                transition: 'all 0.2s ease'
                              }}
                            >
                              {`${name} ${(percent * 100).toFixed(0)}%`}
                            </text>
                          );
                        }}
                        labelLine={false}
                        onMouseEnter={(_, index) => setActivePieIndex(index)}
                        activeIndex={activePieIndex}
                        activeShape={(props) => {
                          const { cx, cy, outerRadius, startAngle, endAngle, fill } = props;
                          return (
                            <Sector
                              cx={cx}
                              cy={cy}
                              innerRadius={0}
                              outerRadius={outerRadius + 8}
                              startAngle={startAngle}
                              endAngle={endAngle}
                              fill={fill}
                              style={{
                                filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))',
                                transition: 'all 0.2s ease'
                              }}
                            />
                          );
                        }}
                      >
                        {categoryBreakdown.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.color}
                          />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            )}

            {/* 3. Daily Spending Bar Chart - RIGHT */}
            {dailySpending.length > 0 && (
              <ChartCard title="Daily Spending" subtitle="Spending over time">
                <div className="h-[280px] overflow-hidden">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dailySpending} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value}`}
                      />
                      <Tooltip
                        formatter={(value) => [`$${value.toFixed(2)}`, 'Spent']}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar
                        dataKey="amount"
                        fill="#14b8a6"
                        radius={[4, 4, 0, 0]}
                        maxBarSize={40}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            )}
          </div>
        )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader size={32} className="animate-spin text-primary-600" />
        </div>
      )}

      {/* Transactions Table */}
      {!isLoading && !error && (
        <TransactionsTable
          transactions={transactions}
          categories={categories}
          onCategoryUpdate={handleCategoryUpdate}
          onTransactionUpdate={handleTransactionUpdate}
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && transactions.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-500">No transactions found. Try adjusting your filters or upload a CSV file.</p>
        </div>
      )}
    </div>
  );
};
