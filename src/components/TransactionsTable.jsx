import React, { useState, useRef, useEffect } from 'react';
import { Badge, getCategoryBadgeVariant } from './Badge';
import { Button } from './Button';
import { Sparkles, X, ChevronDown, Brain, Edit2, Check, XCircle } from 'lucide-react';

/**
 * TransactionsTable component with row selection and inline actions
 */
export const TransactionsTable = ({ transactions, categories = [], onCategoryUpdate, onTransactionUpdate }) => {
  const [selectedTransactions, setSelectedTransactions] = useState([]);
  const [expandedRow, setExpandedRow] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingNote, setEditingNote] = useState(null);
  const [noteValue, setNoteValue] = useState('');
  const dropdownRef = useRef(null);
  const noteInputRef = useRef(null);

  const handleRowClick = (transactionId) => {
    setSelectedTransactions(prev => {
      if (prev.includes(transactionId)) {
        return prev.filter(id => id !== transactionId);
      } else {
        return [...prev, transactionId];
      }
    });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setEditingCategory(null);
      }
    };

    if (editingCategory) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [editingCategory]);

  // Focus note input when editing starts
  useEffect(() => {
    if (editingNote && noteInputRef.current) {
      noteInputRef.current.focus();
      noteInputRef.current.select();
    }
  }, [editingNote]);

  // Close note editing when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (editingNote && noteInputRef.current && !noteInputRef.current.parentElement.contains(event.target)) {
        handleNoteCancel();
      }
    };

    if (editingNote) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [editingNote]);

  const handleNoteClick = (e, transaction) => {
    e.stopPropagation();
    setEditingNote(transaction.id);
    setNoteValue(transaction.noteUser || '');
  };

  const handleNoteSave = async (transactionId) => {
    if (onTransactionUpdate) {
      await onTransactionUpdate(transactionId, { noteUser: noteValue });
    }
    setEditingNote(null);
  };

  const handleNoteCancel = () => {
    setEditingNote(null);
    setNoteValue('');
  };

  const handleAIAnalyze = (e, transactionId) => {
    e.stopPropagation();
    alert(`AI analyze feature for transaction ${transactionId} coming soon!`);
  };

  const handleBatchAIAnalyze = () => {
    alert(`AI analyze feature for ${selectedTransactions.length} selected transactions coming soon!`);
  };

  const handleEditTransaction = (e, transactionId) => {
    e.stopPropagation();
    setExpandedRow(expandedRow === transactionId ? null : transactionId);
  };

  const handleClearSelection = () => {
    setSelectedTransactions([]);
  };

  const formatDate = (dateString) => {
    // Parse YYYY-MM-DD format directly without timezone conversion
    const [year, month, day] = dateString.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const formatAmount = (amount) => {
    const absAmount = Math.abs(amount);
    const formatted = absAmount.toFixed(2);
    return amount < 0 ? `-$${formatted}` : `$${formatted}`;
  };

  const handleCategoryClick = (e, transactionId) => {
    e.stopPropagation(); // Prevent row expansion
    setEditingCategory(editingCategory === transactionId ? null : transactionId);
  };

  const handleCategorySelect = async (transactionId, newCategory) => {
    setEditingCategory(null);
    if (onCategoryUpdate) {
      await onCategoryUpdate(transactionId, newCategory);
    }
  };

  if (transactions.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
        <p className="text-gray-500">No transactions found matching your filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Batch Action Toolbar - Always visible */}
      <div className={`rounded-xl px-6 h-[52px] flex items-center transition-all ${
        selectedTransactions.length > 0
          ? 'bg-primary-50 border border-primary-200'
          : 'bg-gray-50 border border-gray-200'
      }`}>
        <div className="flex items-center justify-between w-full">
          {selectedTransactions.length > 0 ? (
            <>
              <span className="text-sm font-medium text-primary-900">
                {selectedTransactions.length} transaction{selectedTransactions.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-3">
                <Button
                  variant="primary"
                  size="sm"
                  icon={<Brain size={14} />}
                  onClick={handleBatchAIAnalyze}
                >
                  AI Analyze Selected
                </Button>
                <button
                  onClick={handleClearSelection}
                  className="text-sm text-primary-700 hover:text-primary-900 font-medium"
                >
                  Clear Selection
                </button>
              </div>
            </>
          ) : (
            <span className="text-sm text-gray-500">
              Please select a transaction
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Note
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Merchant
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {transactions.map((transaction) => {
              const isSelected = selectedTransactions.includes(transaction.id);
              return (
              <React.Fragment key={transaction.id}>
                <tr
                  onClick={() => handleRowClick(transaction.id)}
                  className={`cursor-pointer transition-colors border-l-4 ${
                    isSelected
                      ? 'bg-primary-50 hover:bg-primary-100 border-l-primary-500'
                      : 'hover:bg-gray-50 border-l-white hover:border-l-gray-50'
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(transaction.date)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="flex items-center gap-2 min-h-[32px]">
                      {editingNote === transaction.id ? (
                        <>
                          <input
                            ref={noteInputRef}
                            type="text"
                            value={noteValue}
                            onChange={(e) => setNoteValue(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleNoteSave(transaction.id);
                              if (e.key === 'Escape') handleNoteCancel();
                            }}
                            className="flex-1 px-2 py-1 border border-primary-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm h-[32px]"
                          />
                          <button
                            onClick={(e) => { e.stopPropagation(); handleNoteSave(transaction.id); }}
                            className="text-green-600 hover:text-green-700 flex-shrink-0 w-4"
                          >
                            <Check size={16} />
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleNoteCancel(); }}
                            className="text-red-600 hover:text-red-700 flex-shrink-0 w-4"
                          >
                            <XCircle size={16} />
                          </button>
                        </>
                      ) : (
                        <>
                          <div
                            onClick={(e) => handleNoteClick(e, transaction)}
                            className="cursor-text hover:bg-gray-100 px-2 py-1 rounded transition-colors flex-1 min-w-0"
                          >
                            {transaction.noteUser || <span className="text-gray-400 italic">Click to add note</span>}
                          </div>
                          {/* Reserve space for buttons to prevent width change */}
                          <div className="w-4 flex-shrink-0"></div>
                          <div className="w-4 flex-shrink-0"></div>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="relative inline-block" ref={editingCategory === transaction.id ? dropdownRef : null}>
                      <div
                        onClick={(e) => handleCategoryClick(e, transaction.id)}
                        className="inline-flex items-center cursor-pointer hover:opacity-80 transition-opacity"
                      >
                        <Badge variant={getCategoryBadgeVariant(transaction.category)}>
                          <span className="flex items-center gap-1">
                            {transaction.category}
                            <ChevronDown size={12} className={`transition-transform ${editingCategory === transaction.id ? 'rotate-180' : ''}`} />
                          </span>
                        </Badge>
                      </div>

                      {editingCategory === transaction.id && (
                        <div
                          className="absolute z-50 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto flex flex-col"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {categories.map(cat => (
                            <button
                              key={cat}
                              onClick={() => handleCategorySelect(transaction.id, cat)}
                              className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 transition-colors flex-shrink-0 ${
                                cat === transaction.category ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                              }`}
                            >
                              {cat}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {transaction.merchant}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={(e) => handleAIAnalyze(e, transaction.id)}
                        className="p-1.5 text-primary-600 hover:bg-primary-50 rounded transition-colors"
                        title="AI Analyze"
                      >
                        <Brain size={16} />
                      </button>
                      <button
                        onClick={(e) => handleEditTransaction(e, transaction.id)}
                        className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                        title="View Details"
                      >
                        <Edit2 size={16} />
                      </button>
                    </div>
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-right ${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {formatAmount(transaction.amount)}
                  </td>
                </tr>
                {expandedRow === transaction.id && (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 bg-gray-50">
                      <TransactionDetails
                        transaction={transaction}
                        onClose={() => setExpandedRow(null)}
                        onUpdate={onTransactionUpdate}
                      />
                    </td>
                  </tr>
                )}
              </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden divide-y divide-gray-200">
        {transactions.map((transaction) => {
          const isSelected = selectedTransactions.includes(transaction.id);
          return (
          <div key={transaction.id} className={`p-4 transition-colors border-l-4 ${
            isSelected ? 'bg-primary-50 border-l-primary-500' : 'border-l-white'
          }`}>
            <div
              onClick={() => handleRowClick(transaction.id)}
              className="cursor-pointer"
            >
              <div className="flex items-start gap-3 mb-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 min-h-[32px]">
                    {editingNote === transaction.id ? (
                      <>
                        <input
                          ref={noteInputRef}
                          type="text"
                          value={noteValue}
                          onChange={(e) => setNoteValue(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleNoteSave(transaction.id);
                            if (e.key === 'Escape') handleNoteCancel();
                          }}
                          className="flex-1 px-2 py-1 border border-primary-300 rounded focus:ring-2 focus:ring-primary-500 text-sm h-[32px]"
                        />
                        <button
                          onClick={(e) => { e.stopPropagation(); handleNoteSave(transaction.id); }}
                          className="text-green-600 flex-shrink-0 w-4"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleNoteCancel(); }}
                          className="text-red-600 flex-shrink-0 w-4"
                        >
                          <XCircle size={16} />
                        </button>
                      </>
                    ) : (
                      <>
                        <div
                          onClick={(e) => handleNoteClick(e, transaction)}
                          className="text-sm font-medium text-gray-900 hover:bg-gray-100 px-2 py-1 rounded transition-colors flex-1 min-w-0"
                        >
                          {transaction.noteUser || <span className="text-gray-400 italic">Click to add note</span>}
                        </div>
                        {/* Reserve space for buttons to prevent width change */}
                        <div className="w-4 flex-shrink-0"></div>
                        <div className="w-4 flex-shrink-0"></div>
                      </>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">{transaction.merchant}</p>
                </div>
                <p className={`text-sm font-semibold ${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {formatAmount(transaction.amount)}
                </p>
              </div>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <p className="text-xs text-gray-500">{formatDate(transaction.date)}</p>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={(e) => handleAIAnalyze(e, transaction.id)}
                      className="p-1 text-primary-600 hover:bg-primary-50 rounded"
                      title="AI Analyze"
                    >
                      <Brain size={14} />
                    </button>
                    <button
                      onClick={(e) => handleEditTransaction(e, transaction.id)}
                      className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                      title="View Details"
                    >
                      <Edit2 size={14} />
                    </button>
                  </div>
                </div>
                <div className="relative inline-block" ref={editingCategory === transaction.id ? dropdownRef : null}>
                  <div
                    onClick={(e) => handleCategoryClick(e, transaction.id)}
                    className="inline-flex items-center cursor-pointer hover:opacity-80 transition-opacity"
                  >
                    <Badge variant={getCategoryBadgeVariant(transaction.category)} size="sm">
                      <span className="flex items-center gap-1">
                        {transaction.category}
                        <ChevronDown size={10} className={`transition-transform ${editingCategory === transaction.id ? 'rotate-180' : ''}`} />
                      </span>
                    </Badge>
                  </div>

                  {editingCategory === transaction.id && (
                    <div
                      className="absolute right-0 z-50 mt-1 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-48 overflow-y-auto flex flex-col"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {categories.map(cat => (
                        <button
                          key={cat}
                          onClick={() => handleCategorySelect(transaction.id, cat)}
                          className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-50 transition-colors flex-shrink-0 ${
                            cat === transaction.category ? 'bg-primary-50 text-primary-700 font-medium' : 'text-gray-700'
                          }`}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
            {expandedRow === transaction.id && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <TransactionDetails
                  transaction={transaction}
                  onClose={() => setExpandedRow(null)}
                  onUpdate={onTransactionUpdate}
                />
              </div>
            )}
          </div>
          );
        })}
      </div>
      </div>
    </div>
  );
};

/**
 * Transaction details panel
 */
const TransactionDetails = ({ transaction, onClose, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDate, setEditedDate] = useState(transaction.date);
  const [editedAmount, setEditedAmount] = useState(transaction.amount);

  const formatDateForInput = (dateString) => {
    // If already in YYYY-MM-DD format, return as-is
    if (typeof dateString === 'string' && dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return dateString;
    }
    // Otherwise parse and format
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
  };

  const formatAmount = (amount) => {
    const absAmount = Math.abs(amount);
    const formatted = absAmount.toFixed(2);
    return amount < 0 ? `-$${formatted}` : `$${formatted}`;
  };

  const handleApply = async () => {
    if (onUpdate) {
      await onUpdate(transaction.id, {
        date: editedDate,
        amount: parseFloat(editedAmount)
      });
    }
    setIsEditing(false);
    onClose();
  };

  const handleCancel = () => {
    setEditedDate(transaction.date);
    setEditedAmount(transaction.amount);
    setIsEditing(false);
  };

  const handleCategorize = () => {
    alert('AI categorization feature coming soon!');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <h4 className="text-sm font-semibold text-gray-900">Transaction Details</h4>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <X size={16} />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Date
          </label>
          {isEditing ? (
            <input
              type="date"
              value={formatDateForInput(editedDate)}
              onChange={(e) => setEditedDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          ) : (
            <p className="text-sm font-medium text-gray-900">
              {(() => {
                const [year, month, day] = transaction.date.split('-');
                const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
                return date.toLocaleDateString();
              })()}
            </p>
          )}
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Amount
          </label>
          {isEditing ? (
            <input
              type="number"
              step="0.01"
              value={editedAmount}
              onChange={(e) => setEditedAmount(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          ) : (
            <p className={`text-sm font-medium ${transaction.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatAmount(transaction.amount)}
            </p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Merchant
        </label>
        <p className="text-sm font-medium text-gray-700">{transaction.merchant}</p>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Category
        </label>
        <Badge variant={getCategoryBadgeVariant(transaction.category)}>
          {transaction.category}
        </Badge>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Raw Bank Description
        </label>
        <p className="text-sm text-gray-700 bg-gray-100 p-2 rounded">
          {transaction.descriptionRaw}
        </p>
      </div>

      <div className="flex gap-2 pt-2 border-t">
        {isEditing ? (
          <>
            <Button
              variant="primary"
              size="sm"
              onClick={handleApply}
            >
              Apply Changes
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCancel}
            >
              Cancel
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              Edit
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<Sparkles size={14} />}
              onClick={handleCategorize}
            >
              Categorize with AI
            </Button>
          </>
        )}
      </div>
    </div>
  );
};
