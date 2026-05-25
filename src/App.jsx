import React, { useState, useEffect, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useSearchParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { FilterPanel } from './components/FilterPanel';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { UploadPage } from './pages/UploadPage';
import { RecurringPage } from './pages/RecurringPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { SettingsPage } from './pages/SettingsPage';
import { CardsPage } from './pages/CardsPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { GoogleCallback } from './pages/GoogleCallback';
import { categoriesAPI } from './services/api';

const DEFAULT_FILTERS = {
  dateRange: 'this_month',
  startDate: '',
  endDate: '',
  transactionType: 'all',
  categories: [],
  merchant: '',
  amountMin: '',
  amountMax: ''
};

// Serialize filters to URL query params, omitting defaults/empties for clean URLs.
const filtersToSearchParams = (f) => {
  const sp = new URLSearchParams();
  if (f.dateRange && f.dateRange !== 'this_month') sp.set('dateRange', f.dateRange);
  if (f.startDate) sp.set('startDate', f.startDate);
  if (f.endDate) sp.set('endDate', f.endDate);
  if (f.transactionType && f.transactionType !== 'all') sp.set('transactionType', f.transactionType);
  (f.categories || []).forEach((c) => sp.append('category', c));
  if (f.merchant) sp.set('merchant', f.merchant);
  if (f.amountMin) sp.set('amountMin', f.amountMin);
  if (f.amountMax) sp.set('amountMax', f.amountMax);
  return sp;
};

// Parse filters back from URL query params, falling back to defaults.
const searchParamsToFilters = (sp) => ({
  dateRange: sp.get('dateRange') || 'this_month',
  startDate: sp.get('startDate') || '',
  endDate: sp.get('endDate') || '',
  transactionType: sp.get('transactionType') || 'all',
  categories: sp.getAll('category'),
  merchant: sp.get('merchant') || '',
  amountMin: sp.get('amountMin') || '',
  amountMax: sp.get('amountMax') || ''
});

/**
 * Layout component that handles filter panel visibility based on route
 */
const AppLayout = ({ children, isSidebarOpen, setIsSidebarOpen }) => {
  const location = useLocation();
  const showFilterPanel = location.pathname === '/transactions';
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Filters are persisted in the URL query string so they survive a page refresh.
  // A bare /transactions link (e.g. from the sidebar) has no query, so filters
  // reset to defaults when navigating away and back.
  const [searchParams, setSearchParams] = useSearchParams();
  const searchStr = searchParams.toString();
  const filters = useMemo(
    () => (showFilterPanel
      ? searchParamsToFilters(new URLSearchParams(searchStr))
      : DEFAULT_FILTERS),
    [showFilterPanel, searchStr]
  );
  const setFilters = (next) => {
    const updated = typeof next === 'function' ? next(filters) : next;
    setSearchParams(filtersToSearchParams(updated), { replace: true });
  };

  // Fetch user categories with colors from API
  const [categories, setCategories] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await categoriesAPI.getAll();
        // Categories are objects: { id, name, color, ... }
        setCategories(response.data.categories || []);
      } catch (err) {
        // Fallback to default category names if API fails
        setCategories([
          { name: 'Groceries', color: '#22c55e' },
          { name: 'Rent', color: '#ef4444' },
          { name: 'Transport', color: '#f59e0b' },
          { name: 'Eating Out', color: '#3b82f6' },
          { name: 'Shopping', color: '#8b5cf6' },
          { name: 'Subscription', color: '#ec4899' },
          { name: 'Utilities', color: '#6366f1' },
          { name: 'Income', color: '#10b981' },
          { name: 'Other', color: '#6b7280' },
        ]);
      }
    };

    if (user) {
      fetchCategories();
    }
  }, [user]);

  const handleResetFilters = () => {
    setSearchParams(new URLSearchParams(), { replace: true });
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Filter Panel - Only on Transactions page */}
      {showFilterPanel && (
        <>
          {/* Mobile Filter Overlay */}
          {isFilterOpen && (
            <div
              className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
              onClick={() => setIsFilterOpen(false)}
            />
          )}

          {/* Desktop: Static panel next to sidebar */}
          <div className="hidden lg:block w-72 flex-shrink-0 border-r border-gray-200 bg-white">
            <FilterPanel
              filters={filters}
              onFilterChange={setFilters}
              onResetFilters={handleResetFilters}
              categories={categories}
              onClose={() => {}}
            />
          </div>

          {/* Mobile: Slide-in drawer from right */}
          <div className={`
            lg:hidden fixed inset-y-0 right-0 z-50
            w-80 max-w-[85vw] border-l border-gray-200 bg-white shadow-xl
            transform transition-transform duration-300 ease-in-out
            ${isFilterOpen ? 'translate-x-0' : 'translate-x-full'}
          `}>
            <FilterPanel
              filters={filters}
              onFilterChange={setFilters}
              onResetFilters={handleResetFilters}
              categories={categories}
              onClose={() => setIsFilterOpen(false)}
            />
          </div>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <TopBar
          onMenuClick={() => setIsSidebarOpen(true)}
          onFilterClick={showFilterPanel ? () => setIsFilterOpen(!isFilterOpen) : null}
          showFilterButton={showFilterPanel}
          categories={categories}
        />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-gray-50">
          <div key={location.pathname} className="max-w-[1600px] mx-auto page-transition">
            {React.cloneElement(children, { filters, setFilters, categories, onResetFilters: handleResetFilters })}
          </div>
        </main>
      </div>
    </div>
  );
};

/**
 * Main App component with routing and layout
 */
function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/auth/google/callback" element={<GoogleCallback />} />

          {/* Protected Routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <DashboardPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/transactions" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <TransactionsPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/recurring" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <RecurringPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/categories" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <CategoriesPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/cards" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <CardsPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/upload" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <UploadPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/users" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <PlaceholderPage title="Users" description="User management coming soon" />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/mail" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <PlaceholderPage title="Mail" description="Email management coming soon" />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <SettingsPage />
              </AppLayout>
            </ProtectedRoute>
          } />
          <Route path="/security" element={
            <ProtectedRoute>
              <AppLayout isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen}>
                <PlaceholderPage title="Security" description="Security settings coming soon" />
              </AppLayout>
            </ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
