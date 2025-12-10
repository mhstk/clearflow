import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { FilterPanel } from './components/FilterPanel';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { UploadPage } from './pages/UploadPage';
import { RecurringPage } from './pages/RecurringPage';
import { SettingsPage } from './pages/SettingsPage';
import { CardsPage } from './pages/CardsPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { GoogleCallback } from './pages/GoogleCallback';

/**
 * Layout component that handles filter panel visibility based on route
 */
const AppLayout = ({ children, isSidebarOpen, setIsSidebarOpen }) => {
  const location = useLocation();
  const showFilterPanel = location.pathname === '/transactions';
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const [filters, setFilters] = useState({
    dateRange: 'this_month',
    startDate: '',
    endDate: '',
    transactionType: 'all',
    categories: [],
    merchant: '',
    amountMin: '',
    amountMax: ''
  });

  const [categories] = useState(['Groceries', 'Rent', 'Transport', 'Eating Out', 'Shopping', 'Subscription', 'Utilities', 'Income', 'Other', 'Uncategorized']);

  const handleResetFilters = () => {
    setFilters({
      dateRange: 'this_month',
      startDate: '',
      endDate: '',
      transactionType: 'all',
      categories: [],
      merchant: '',
      amountMin: '',
      amountMax: ''
    });
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
