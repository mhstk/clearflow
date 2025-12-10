import axios from 'axios';

// Get API base URL from environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session-based auth
  paramsSerializer: {
    // FastAPI expects repeated params: category=A&category=B (not category[]=A&category[]=B)
    indexes: null,
  },
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login on unauthorized
      localStorage.removeItem('auth_token');
      // Only redirect if not already on auth pages
      if (!window.location.pathname.startsWith('/login') &&
          !window.location.pathname.startsWith('/signup') &&
          !window.location.pathname.startsWith('/auth')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Auth API
 */
export const authAPI = {
  /**
   * Login with email and password
   */
  login: (credentials) => apiClient.post('/api/v1/auth/login', credentials),

  /**
   * Sign up with email, password, and optional name
   */
  signup: (userData) => apiClient.post('/api/v1/auth/signup', userData),

  /**
   * Authenticate with Google OAuth code
   */
  googleAuth: (data) => apiClient.post('/api/v1/auth/google', data),

  /**
   * Get Google OAuth URL
   */
  getGoogleUrl: () => apiClient.get('/api/v1/auth/google/url'),

  /**
   * Get current authenticated user
   */
  me: () => apiClient.get('/api/v1/auth/me'),
};

/**
 * Account API
 */
export const accountsAPI = {
  getAll: () => apiClient.get('/api/v1/accounts/'),
  getById: (accountId) => apiClient.get(`/api/v1/accounts/${accountId}`),
  create: (data) => apiClient.post('/api/v1/accounts/', data),
};

/**
 * Transactions API
 */
export const transactionsAPI = {
  /**
   * Get filtered transactions with aggregates
   * @param {Object} params - Filter parameters
   * @param {number} params.account_id - Account ID
   * @param {string} params.start_date - Start date (YYYY-MM-DD)
   * @param {string} params.end_date - End date (YYYY-MM-DD)
   * @param {string} params.date_range - Date range enum (this_month, last_month, last_3_months, last_6_months, this_year, all_time)
   * @param {string[]} params.category - Category filters (array)
   * @param {string} params.merchant_query - Merchant search query
   * @param {number} params.min_amount - Minimum amount
   * @param {number} params.max_amount - Maximum amount
   * @param {number} params.page - Page number (default: 1)
   * @param {number} params.page_size - Page size (default: 50)
   */
  getView: (params = {}) => {
    // Convert category array to proper format if needed
    const queryParams = { ...params };
    if (queryParams.category && Array.isArray(queryParams.category)) {
      // Axios will handle array params correctly
      queryParams.category = queryParams.category;
    }
    return apiClient.get('/api/v1/transactions/view', { params: queryParams });
  },

  /**
   * Get single transaction by ID
   */
  getById: (transactionId) => apiClient.get(`/api/v1/transactions/${transactionId}`),

  /**
   * Create a new transaction manually
   * @param {Object} data - Transaction data
   * @param {string} data.date - Transaction date (YYYY-MM-DD)
   * @param {number} data.amount - Amount (positive for income, negative for expense)
   * @param {string} data.description - Merchant/description
   * @param {string} data.category - Category name
   * @param {string} data.note - Optional user note
   */
  create: (data) => apiClient.post('/api/v1/transactions/', data),

  /**
   * Get all categories with counts
   */
  getCategories: () => apiClient.get('/api/v1/transactions/categories/list'),

  /**
   * Detect recurring transactions
   */
  detectRecurring: (minOccurrences = 3) =>
    apiClient.get('/api/v1/transactions/recurring/detect', {
      params: { min_occurrences: minOccurrences },
    }),

  /**
   * Upload CSV file
   * @param {File} file - CSV file
   * @param {number} accountId - Account ID
   * @param {boolean} autoCategorize - Auto categorize with AI (default: true)
   */
  uploadCSV: (file, accountId, autoCategorize = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('auto_categorize', autoCategorize);
    if (accountId) {
      formData.append('account_id', accountId);
    }
    return apiClient.post('/api/v1/transactions/upload_csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Update transaction note
   */
  updateNote: (transactionId, noteUser) =>
    apiClient.patch(`/api/v1/transactions/${transactionId}/note`, { note_user: noteUser }),

  /**
   * Update transaction category
   */
  updateCategory: (transactionId, category) =>
    apiClient.patch(`/api/v1/transactions/${transactionId}/category`, { category }),

  /**
   * Update transaction details (date and/or amount)
   */
  updateTransaction: (transactionId, updates) =>
    apiClient.patch(`/api/v1/transactions/${transactionId}`, updates),
};

/**
 * Dashboard API
 */
export const dashboardAPI = {
  /**
   * Get dashboard stats for a date range
   * @param {string} dateRange - Date range filter (e.g., 'last_30_days', 'last_7_days', 'this_month')
   */
  getStats: (dateRange = 'last_30_days') =>
    apiClient.get('/api/v1/dashboard/stats', { params: { date_range: dateRange } }),

  /**
   * Get dashboard stats for specific period
   * @param {number} months - Number of months to look back
   */
  getStatsPeriod: (months = 1) =>
    apiClient.get('/api/v1/dashboard/stats/period', { params: { months } }),
};

/**
 * AI API
 */
export const aiAPI = {
  /**
   * Categorize merchant using AI
   */
  categorizeMerchant: (merchantKey, sampleDescriptions) =>
    apiClient.post('/api/v1/ai/categorize_merchant', {
      merchant_key: merchantKey,
      sample_descriptions: sampleDescriptions,
    }),

  /**
   * Batch categorize transactions using AI
   * @param {number[]} transactionIds - Array of transaction IDs to categorize
   * @param {boolean} autoApply - Automatically apply the AI suggestions (default: true)
   */
  categorizeBatch: (transactionIds, autoApply = true) =>
    apiClient.post('/api/v1/ai/categorize_batch', {
      transaction_ids: transactionIds,
      auto_apply: autoApply,
    }),

  /**
   * Get available categories from AI
   */
  getCategories: () => apiClient.get('/api/v1/ai/categories'),

  /**
   * Get AI insights
   */
  getInsights: (filters = {}) =>
    apiClient.post('/api/v1/ai/insights', filters),
};

/**
 * Recurring Payments API
 */
export const recurringAPI = {
  /**
   * Get all detected recurring payments
   * @param {boolean} forceRefresh - Force re-analysis ignoring cache
   */
  getRecurringPayments: (forceRefresh = false) =>
    apiClient.get('/api/v1/recurring/', { params: { force_refresh: forceRefresh } }),

  /**
   * Trigger full recurring payment analysis in background
   */
  analyzeRecurring: () =>
    apiClient.post('/api/v1/recurring/analyze'),

  /**
   * Get AI-generated insights about recurring payments
   * @param {boolean} forceRefresh - Force regeneration of insights
   */
  getInsights: (forceRefresh = false) =>
    apiClient.get('/api/v1/recurring/insights', { params: { force_refresh: forceRefresh } }),

  /**
   * Get upcoming recurring payments
   * @param {number} days - Days to look ahead (1-30)
   */
  getUpcoming: (days = 7) =>
    apiClient.get('/api/v1/recurring/upcoming', { params: { days } }),
};

/**
 * Utility functions
 */

/**
 * Format currency value
 */
export const formatCurrency = (value, currency = 'CAD') => {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: currency,
  }).format(value);
};

/**
 * Transform backend transaction to frontend format
 */
export const transformTransaction = (transaction) => ({
  id: transaction.id,
  date: transaction.date,
  descriptionRaw: transaction.description_raw,
  merchant: transaction.merchant_key,
  amount: transaction.amount,
  currency: transaction.currency,
  category: transaction.category,
  noteUser: transaction.note_user,
  accountId: transaction.account_id,
  userId: transaction.user_id,
  createdAt: transaction.created_at,
  categorySource: transaction.category_source,
});

export default apiClient;
