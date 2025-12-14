import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, HelpCircle, Menu, Filter, Settings, LogOut, Plus } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { AddTransactionModal } from './AddTransactionModal';

/**
 * TopBar component matching reference design
 */
export const TopBar = ({ title, subtitle, onMenuClick, showActions = true, onFilterClick, showFilterButton, onTransactionAdded }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const profileDropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(event.target)) {
        setProfileDropdownOpen(false);
      }
    };

    if (profileDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [profileDropdownOpen]);

  const handleLogout = () => {
    setProfileDropdownOpen(false);
    logout();
  };

  const handleSettings = () => {
    setProfileDropdownOpen(false);
    navigate('/settings');
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <div className="bg-white border-b border-gray-100 px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
      <div className="flex items-center justify-between">
        {/* Left: Greeting */}
        <div className="flex items-center flex-1 min-w-0">
          <button
            onClick={onMenuClick}
            className="md:hidden mr-3 text-gray-500 hover:text-gray-700 flex-shrink-0"
          >
            <Menu size={24} />
          </button>
          {showFilterButton && (
            <button
              onClick={onFilterClick}
              className="lg:hidden mr-3 text-gray-500 hover:text-gray-700 flex-shrink-0"
            >
              <Filter size={22} />
            </button>
          )}
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-gray-900 truncate">
              {title || `${getGreeting()}, ${user?.name?.split(' ')[0] || 'there'}!`}
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block">
              {subtitle || "Here's an overview of your financial health and recent activity."}
            </p>
          </div>
        </div>

        {/* Right: Search, Icons, User Profile */}
        {showActions && (
          <div className="flex items-center space-x-3 sm:space-x-4 lg:space-x-6 ml-2">
            {/* Search */}
            <div className="hidden lg:flex items-center bg-gray-50 rounded-full px-4 py-2.5 w-80 border border-gray-200">
              <Search size={20} className="text-gray-400 mr-2" />
              <input
                type="text"
                placeholder="Search product"
                className="bg-transparent border-none outline-none text-sm text-gray-700 placeholder-gray-400 w-full"
              />
            </div>

            {/* Notification Icon */}
            <button className="relative text-gray-400 hover:text-gray-600 transition-colors hidden sm:block">
              <Bell size={20} className="sm:w-5 sm:h-5 lg:w-6 lg:h-6" />
            </button>

            {/* Help Icon */}
            <button className="text-gray-400 hover:text-gray-600 transition-colors hidden sm:block">
              <HelpCircle size={20} className="sm:w-5 sm:h-5 lg:w-6 lg:h-6" />
            </button>

            {/* Add Transaction Button */}
            <button
              onClick={() => setShowAddModal(true)}
              className="w-9 h-9 flex items-center justify-center bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors shadow-sm"
              title="Add Transaction"
            >
              <Plus size={20} />
            </button>

            {/* User Profile */}
            <div className="relative" ref={profileDropdownRef}>
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center space-x-2 sm:space-x-3 pl-3 sm:pl-4 lg:pl-6 border-l border-gray-200 hover:opacity-80 transition-opacity"
              >
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-semibold text-base sm:text-lg">
                    {(user?.name || user?.email || 'M').charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="hidden xl:block text-left">
                  <p className="text-sm font-semibold text-gray-900">{user?.name || 'User'}</p>
                  <span className="inline-block px-2 py-0.5 bg-primary-100 text-primary-700 text-xs font-medium rounded">
                    PRO
                  </span>
                </div>
              </button>

              {/* Profile Dropdown */}
              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{user?.name || 'User'}</p>
                    <p className="text-xs text-gray-500 truncate">{user?.email || ''}</p>
                  </div>
                  <button
                    onClick={handleSettings}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <Settings size={18} className="text-gray-400" />
                    Settings
                  </button>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut size={18} />
                    Log out
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Add Transaction Modal */}
      <AddTransactionModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          if (onTransactionAdded) {
            onTransactionAdded();
          }
        }}
      />
    </div>
  );
};
