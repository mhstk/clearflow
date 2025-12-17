import React, { useState, useEffect } from 'react';
import { Pencil, Trash2, Plus, RotateCcw, GripVertical, X, Check } from 'lucide-react';
import { Button } from '../components/Button';
import { categoriesAPI } from '../services/api';

/**
 * Categories management page
 * Users can add, edit, delete, and reorder their custom categories.
 * System categories (like "Other") are shown but cannot be modified.
 */
export const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', color: '' });
  const [newCategory, setNewCategory] = useState({ name: '', color: '#6b7280' });
  const [isAdding, setIsAdding] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  // Predefined colors for quick selection
  const colorPresets = [
    '#22c55e', '#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6',
    '#ec4899', '#6366f1', '#10b981', '#14b8a6', '#f97316',
    '#84cc16', '#06b6d4', '#a855f7', '#6b7280'
  ];

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await categoriesAPI.getAll();
      setCategories(response.data.categories);
      setError(null);
    } catch (err) {
      setError('Failed to load categories');
      console.error('Error fetching categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newCategory.name.trim()) return;

    try {
      await categoriesAPI.create(newCategory);
      setNewCategory({ name: '', color: '#6b7280' });
      setIsAdding(false);
      fetchCategories();
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create category';
      setError(message);
    }
  };

  const handleUpdate = async (categoryId) => {
    if (!editForm.name.trim()) return;

    try {
      await categoriesAPI.update(categoryId, editForm);
      setEditingId(null);
      fetchCategories();
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to update category';
      setError(message);
    }
  };

  const handleDelete = async (categoryId) => {
    if (!confirm('Delete this category? Transactions with this category will be set to "Uncategorized".')) {
      return;
    }

    try {
      await categoriesAPI.delete(categoryId);
      fetchCategories();
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to delete category';
      setError(message);
    }
  };

  const handleReset = async () => {
    try {
      await categoriesAPI.reset();
      setShowResetConfirm(false);
      fetchCategories();
    } catch (err) {
      setError('Failed to reset categories');
    }
  };

  const startEditing = (category) => {
    setEditingId(category.id);
    setEditForm({ name: category.name, color: category.color || '#6b7280' });
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditForm({ name: '', color: '' });
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-14 bg-gray-100 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Manage Categories</h2>
        <p className="text-gray-600">
          Customize the categories used for your transactions. These categories are used by AI categorization and appear in all dropdowns.
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
          <span className="text-red-700">{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <X size={18} />
          </button>
        </div>
      )}

      {/* Categories List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="space-y-3">
          {categories.map((category) => (
            <div
              key={category.id}
              className={`rounded-xl border p-4 flex items-center justify-between transition-all ${
                category.is_system
                  ? 'bg-gray-50 border-gray-200'
                  : 'bg-white border-gray-200 hover:shadow-md hover:border-gray-300'
              }`}
            >
              {editingId === category.id ? (
                // Edit mode
                <div className="flex-1 flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={editForm.color}
                      onChange={(e) => setEditForm({ ...editForm, color: e.target.value })}
                      className="w-8 h-8 rounded cursor-pointer border-0"
                    />
                  </div>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleUpdate(category.id);
                      if (e.key === 'Escape') cancelEditing();
                    }}
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleUpdate(category.id)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    >
                      <Check size={18} />
                    </button>
                    <button
                      onClick={cancelEditing}
                      className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg"
                    >
                      <X size={18} />
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <>
                  <div className="flex items-center gap-3">
                    <span
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: category.color || '#6b7280' }}
                    />
                    <span className={`font-medium ${category.is_system ? 'text-gray-500' : 'text-gray-900'}`}>
                      {category.name}
                    </span>
                    {category.is_system && (
                      <span className="text-xs bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full">
                        System
                      </span>
                    )}
                  </div>
                  {!category.is_system && (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => startEditing(category)}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Edit category"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(category.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete category"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}

          {/* Add Category Form */}
          {isAdding ? (
            <div className="rounded-xl border border-primary-200 bg-primary-50 p-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={newCategory.color}
                    onChange={(e) => setNewCategory({ ...newCategory, color: e.target.value })}
                    className="w-8 h-8 rounded cursor-pointer border-0"
                  />
                </div>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                  placeholder="Category name"
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreate();
                    if (e.key === 'Escape') setIsAdding(false);
                  }}
                />
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleCreate}
                    className="p-2 text-green-600 hover:bg-green-100 rounded-lg"
                  >
                    <Check size={18} />
                  </button>
                  <button
                    onClick={() => {
                      setIsAdding(false);
                      setNewCategory({ name: '', color: '#6b7280' });
                    }}
                    className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>
              {/* Color presets */}
              <div className="mt-3 flex flex-wrap gap-2">
                {colorPresets.map((color) => (
                  <button
                    key={color}
                    onClick={() => setNewCategory({ ...newCategory, color })}
                    className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-110 ${
                      newCategory.color === color ? 'border-gray-900 scale-110' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsAdding(true)}
              className="w-full rounded-xl border-2 border-dashed border-gray-300 p-4 flex items-center justify-center gap-2 text-gray-500 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50 transition-colors"
            >
              <Plus size={20} />
              <span>Add Category</span>
            </button>
          )}
        </div>
      </div>

      {/* Reset to Defaults */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Reset Categories</h3>
            <p className="text-sm text-gray-500">
              Reset all categories to default values. Transactions will be set to "Uncategorized".
            </p>
          </div>
          {showResetConfirm ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600">Are you sure?</span>
              <Button variant="danger" size="sm" onClick={handleReset}>
                Yes, Reset
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setShowResetConfirm(false)}>
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              variant="ghost"
              onClick={() => setShowResetConfirm(true)}
              className="text-gray-600 hover:text-red-600"
            >
              <RotateCcw size={16} className="mr-2" />
              Reset to Defaults
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
