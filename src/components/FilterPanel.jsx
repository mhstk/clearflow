import React, { useState, useRef, useEffect } from 'react';
import { Button } from './Button';
import { X, ChevronDown, Calendar } from 'lucide-react';
import DatePicker from 'react-datepicker';

/**
 * FilterPanel component for transaction filtering
 */
export const FilterPanel = ({
  filters,
  onFilterChange,
  onResetFilters,
  categories,
  onClose
}) => {
  const [openDropdown, setOpenDropdown] = useState(null);
  const dateRangeDropdownRef = useRef(null);
  const transactionTypeDropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (openDropdown === 'dateRange' && dateRangeDropdownRef.current && !dateRangeDropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      }
      if (openDropdown === 'transactionType' && transactionTypeDropdownRef.current && !transactionTypeDropdownRef.current.contains(event.target)) {
        setOpenDropdown(null);
      }
    };

    if (openDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [openDropdown]);

  const handleCategoryToggle = (category) => {
    const newCategories = filters.categories.includes(category)
      ? filters.categories.filter(c => c !== category)
      : [...filters.categories, category];

    onFilterChange({ ...filters, categories: newCategories });
  };

  // Calculate start and end dates based on date range selection
  const getDateRangeDates = (rangeValue) => {
    const today = new Date();
    const formatDate = (date) => date.toISOString().split('T')[0];

    switch (rangeValue) {
      case 'this_month': {
        const startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        return { startDate: formatDate(startDate), endDate: formatDate(today) };
      }
      case 'last_month': {
        const startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const endDate = new Date(today.getFullYear(), today.getMonth(), 0);
        return { startDate: formatDate(startDate), endDate: formatDate(endDate) };
      }
      case 'last_3_months': {
        const startDate = new Date(today.getFullYear(), today.getMonth() - 2, 1);
        return { startDate: formatDate(startDate), endDate: formatDate(today) };
      }
      case 'last_6_months': {
        const startDate = new Date(today.getFullYear(), today.getMonth() - 5, 1);
        return { startDate: formatDate(startDate), endDate: formatDate(today) };
      }
      case 'this_year': {
        const startDate = new Date(today.getFullYear(), 0, 1);
        return { startDate: formatDate(startDate), endDate: formatDate(today) };
      }
      case 'all_time':
      default:
        return { startDate: '', endDate: '' };
    }
  };

  const handleDateRangeChange = (rangeValue) => {
    const { startDate, endDate } = getDateRangeDates(rangeValue);
    onFilterChange({
      ...filters,
      dateRange: rangeValue,
      startDate,
      endDate
    });
    setOpenDropdown(null);
  };

  const dateRangeOptions = [
    { label: 'This Month', value: 'this_month' },
    { label: 'Last Month', value: 'last_month' },
    { label: 'Last 3 Months', value: 'last_3_months' },
    { label: 'Last 6 Months', value: 'last_6_months' },
    { label: 'This Year', value: 'this_year' },
    { label: 'All Time', value: 'all_time' }
  ];

  const transactionTypeOptions = [
    { label: 'All Transactions', value: 'all' },
    { label: 'Expenses Only', value: 'expenses' },
    { label: 'Income Only', value: 'income' }
  ];

  return (
    <div className="bg-white h-full flex flex-col">
      {/* Header */}
      <div className="p-4 sm:p-5 border-b border-gray-100 lg:border-b-0">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
          <button
            onClick={onClose}
            className="lg:hidden text-gray-400 hover:text-gray-600 p-1 -mr-1"
          >
            <X size={24} />
          </button>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5 pt-2">

        {/* Date Range */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Date Range
          </label>
          <div className="relative" ref={dateRangeDropdownRef}>
            <button
              type="button"
              onClick={() => setOpenDropdown(openDropdown === 'dateRange' ? null : 'dateRange')}
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
            >
              <span className="text-gray-900">
                {dateRangeOptions.find(opt => opt.value === filters.dateRange)?.label || 'Select range'}
              </span>
              <ChevronDown size={16} className={`text-gray-500 transition-transform ${openDropdown === 'dateRange' ? 'rotate-180' : ''}`} />
            </button>

            {openDropdown === 'dateRange' && (
              <div className="absolute z-50 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto">
                {dateRangeOptions.map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleDateRangeChange(option.value)}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors ${
                      option.value === filters.dateRange ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Start Date & End Date Pickers - Always visible */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Start & End Date
          </label>
          <div className="space-y-3 w-full">
            <div className='w-full'>
              <label className="block text-xs text-gray-600 mb-1">Start Date</label>
              <div className="relative w-full">
                <DatePicker
                  selected={filters.startDate ? new Date(filters.startDate + 'T00:00:00') : null}
                  onChange={(date) => {
                    const formatted = date ? date.toISOString().split('T')[0] : '';
                    onFilterChange({ ...filters, startDate: formatted });
                  }}
                  dateFormat="MMM d, yyyy"
                  placeholderText="Select start date"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  calendarClassName="custom-datepicker"
                  showPopperArrow={false}
                  maxDate={filters.endDate ? new Date(filters.endDate + 'T00:00:00') : null}
                />
                <Calendar size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">End Date</label>
              <div className="relative">
                <DatePicker
                  selected={filters.endDate ? new Date(filters.endDate + 'T00:00:00') : null}
                  onChange={(date) => {
                    const formatted = date ? date.toISOString().split('T')[0] : '';
                    onFilterChange({ ...filters, endDate: formatted });
                  }}
                  dateFormat="MMM d, yyyy"
                  placeholderText="Select end date"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  calendarClassName="custom-datepicker"
                  showPopperArrow={false}
                  minDate={filters.startDate ? new Date(filters.startDate + 'T00:00:00') : null}
                />
                <Calendar size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {/* Transaction Type */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Transaction Type
          </label>
          <div className="relative" ref={transactionTypeDropdownRef}>
            <button
              type="button"
              onClick={() => setOpenDropdown(openDropdown === 'transactionType' ? null : 'transactionType')}
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
            >
              <span className="text-gray-900">
                {transactionTypeOptions.find(opt => opt.value === (filters.transactionType || 'all'))?.label || 'Select type'}
              </span>
              <ChevronDown size={16} className={`text-gray-500 transition-transform ${openDropdown === 'transactionType' ? 'rotate-180' : ''}`} />
            </button>

            {openDropdown === 'transactionType' && (
              <div className="absolute z-50 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto">
                {transactionTypeOptions.map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onFilterChange({ ...filters, transactionType: option.value });
                      setOpenDropdown(null);
                    }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors ${
                      option.value === (filters.transactionType || 'all') ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Categories */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Categories
          </label>
          <div className="space-y-2.5">
            {categories.map(category => (
              <label key={category} className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.categories.includes(category)}
                  onChange={() => handleCategoryToggle(category)}
                  className="w-4 h-4 text-primary-500 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="ml-3 text-sm text-gray-700">{category}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Merchant Search */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Merchant
          </label>
          <input
            type="text"
            value={filters.merchant}
            onChange={(e) => onFilterChange({ ...filters, merchant: e.target.value })}
            placeholder="Search merchant..."
            className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Amount Range */}
        <div className="mb-4 sm:mb-6">
          <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-2">
            Amount Range
          </label>
          <div className="flex items-center space-x-2">
            <input
              type="number"
              value={filters.amountMin}
              onChange={(e) => onFilterChange({ ...filters, amountMin: e.target.value })}
              placeholder="Min"
              step="0.01"
              min="0"
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <span className="text-gray-500 text-sm">-</span>
            <input
              type="number"
              value={filters.amountMax}
              onChange={(e) => onFilterChange({ ...filters, amountMax: e.target.value })}
              placeholder="Max"
              step="0.01"
              min="0"
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">Enter positive amounts only</p>
        </div>

        {/* Reset Button - Desktop only */}
        <Button
          variant="ghost"
          className="w-full justify-center hidden lg:flex"
          onClick={onResetFilters}
        >
          Reset Filters
        </Button>
      </div>

      {/* Mobile Footer with Apply & Reset */}
      <div className="lg:hidden p-4 border-t border-gray-200 bg-white space-y-2">
        <Button
          variant="primary"
          className="w-full justify-center"
          onClick={onClose}
        >
          Apply Filters
        </Button>
        <Button
          variant="ghost"
          className="w-full justify-center"
          onClick={() => {
            onResetFilters();
            onClose();
          }}
        >
          Reset Filters
        </Button>
      </div>
    </div>
  );
};
