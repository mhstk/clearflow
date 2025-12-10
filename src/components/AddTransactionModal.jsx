import React, { useState, useEffect, useRef } from 'react';
import { X, TrendingDown, TrendingUp, Loader, ChevronDown } from 'lucide-react';
import DatePicker from 'react-datepicker';
import { transactionsAPI } from '../services/api';

const CATEGORIES = [
  'Groceries',
  'Rent',
  'Transport',
  'Eating Out',
  'Shopping',
  'Subscription',
  'Utilities',
  'Income',
  'Entertainment',
  'Healthcare',
  'Education',
  'Travel',
  'Other',
  'Uncategorized'
];

/**
 * Modal for manually adding a new transaction
 * Features smooth fade + slide animations
 */
export const AddTransactionModal = ({ isOpen, onClose, onSuccess }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [categoryDropdownOpen, setCategoryDropdownOpen] = useState(false);
  const categoryDropdownRef = useRef(null);

  // Form state
  const [transactionType, setTransactionType] = useState('expense'); // 'expense' or 'income'
  const [date, setDate] = useState(new Date());
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Uncategorized');
  const [note, setNote] = useState('');

  // Close category dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (categoryDropdownRef.current && !categoryDropdownRef.current.contains(event.target)) {
        setCategoryDropdownOpen(false);
      }
    };

    if (categoryDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [categoryDropdownOpen]);

  // Handle open animation
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      // Small delay to trigger CSS transition
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setIsAnimating(true);
        });
      });
    }
  }, [isOpen]);

  // Handle close animation
  const handleClose = () => {
    setIsAnimating(false);
    // Wait for animation to complete before hiding
    setTimeout(() => {
      setIsVisible(false);
      resetForm();
      onClose();
    }, 200);
  };

  const resetForm = () => {
    setTransactionType('expense');
    setDate(new Date());
    setAmount('');
    setDescription('');
    setCategory('Uncategorized');
    setNote('');
    setError(null);
    setCategoryDropdownOpen(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!amount || parseFloat(amount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }
    if (!description.trim()) {
      setError('Please enter a description');
      return;
    }

    setIsSubmitting(true);

    try {
      // Calculate final amount (negative for expense, positive for income)
      const finalAmount = transactionType === 'expense'
        ? -Math.abs(parseFloat(amount))
        : Math.abs(parseFloat(amount));

      // Format date as YYYY-MM-DD
      const formattedDate = date.toISOString().split('T')[0];

      await transactionsAPI.create({
        date: formattedDate,
        amount: finalAmount,
        description: description.trim(),
        category: transactionType === 'income' ? 'Income' : category,
        note: note.trim() || null
      });

      // Success - close modal and notify parent
      handleClose();
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create transaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className={`absolute inset-0 bg-black transition-opacity duration-150 ${
          isAnimating ? 'opacity-50' : 'opacity-0'
        }`}
        onClick={handleClose}
      />

      {/* Modal Content */}
      <div
        className={`relative w-full max-w-md bg-white rounded-2xl shadow-xl transition-all duration-200 ${
          isAnimating
            ? 'opacity-100 translate-y-0 scale-100'
            : 'opacity-0 translate-y-4 scale-95'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Add Transaction</h2>
          <button
            onClick={handleClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {/* Transaction Type Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setTransactionType('expense')}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  transactionType === 'expense'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <TrendingDown size={18} />
                Expense
              </button>
              <button
                type="button"
                onClick={() => setTransactionType('income')}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 transition-all ${
                  transactionType === 'income'
                    ? 'border-green-500 bg-green-50 text-green-700'
                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <TrendingUp size={18} />
                Income
              </button>
            </div>
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date
            </label>
            <DatePicker
              selected={date}
              onChange={(d) => setDate(d)}
              dateFormat="MMM d, yyyy"
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              maxDate={new Date()}
            />
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                step="0.01"
                min="0"
                className="w-full pl-8 pr-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Description / Merchant */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {transactionType === 'income' ? 'Source' : 'Merchant / Description'}
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={transactionType === 'income' ? 'e.g., Salary, Freelance' : 'e.g., Grocery Store, Amazon'}
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Category (only for expenses) */}
          {transactionType === 'expense' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <div className="relative" ref={categoryDropdownRef}>
                <button
                  type="button"
                  onClick={() => setCategoryDropdownOpen(!categoryDropdownOpen)}
                  className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white hover:bg-gray-50 transition-colors flex items-center justify-between"
                >
                  <span className="text-gray-900">{category}</span>
                  <ChevronDown
                    size={16}
                    className={`text-gray-500 transition-transform ${categoryDropdownOpen ? 'rotate-180' : ''}`}
                  />
                </button>

                {categoryDropdownOpen && (
                  <div className="absolute z-50 mt-1 w-full bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto">
                    {CATEGORIES.filter(c => c !== 'Income').map(cat => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => {
                          setCategory(cat);
                          setCategoryDropdownOpen(false);
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors ${
                          cat === category ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Note (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Note <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note..."
              rows={2}
              className="w-full px-3 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`flex-1 px-4 py-2.5 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2 ${
                transactionType === 'expense'
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-green-500 hover:bg-green-600'
              }`}
            >
              {isSubmitting ? (
                <>
                  <Loader size={16} className="animate-spin" />
                  Saving...
                </>
              ) : (
                `Add ${transactionType === 'expense' ? 'Expense' : 'Income'}`
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
