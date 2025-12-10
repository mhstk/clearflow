# ClearFlow API Integration Guide

## Setup

### 1. Environment Configuration

Create a `.env` file in the project root (already created):

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 2. Start the Backend Server

Make sure your FastAPI backend is running on `http://localhost:8000`

### 3. Install Dependencies

```bash
npm install
```

### 4. Start the Frontend

```bash
npm run dev
```

## API Client Usage

The API client is located at `src/services/api.js` and provides organized methods for all backend endpoints.

### Accounts API

```javascript
import { accountsAPI } from '../services/api';

// Get all accounts
const accounts = await accountsAPI.getAll();

// Get specific account
const account = await accountsAPI.getById(accountId);

// Create account
const newAccount = await accountsAPI.create({
  name: 'My Checking Account',
  institution: 'TD Bank',
  account_type: 'Checking',
  account_number_last4: '1234',
  currency: 'CAD'
});
```

### Transactions API

```javascript
import { transactionsAPI } from '../services/api';

// Get filtered transactions with aggregates
const response = await transactionsAPI.getView({
  date_range: 'last_3_months', // or 'this_month', 'last_month', 'last_6_months', 'this_year', 'all_time'
  category: ['Groceries', 'Dining'], // Array of categories
  merchant_query: 'amazon',
  min_amount: 10,
  max_amount: 500,
  page: 1,
  page_size: 50
});

// Response structure:
// {
//   filters: { ... },
//   pagination: { page, page_size, total_rows, total_pages },
//   rows: [ ...transactions ],
//   aggregates: {
//     total_spent: 1234.56,
//     total_income: 5678.90,
//     by_category: { 'Groceries': 123.45, ... },
//     by_day: [ { date: '2024-01-01', net: 123.45 }, ... ]
//   }
// }

// Get single transaction
const transaction = await transactionsAPI.getById(transactionId);

// Get all categories with counts
const categories = await transactionsAPI.getCategories();
// Returns: [{ category: 'Groceries', count: 45, total_amount: 123.45 }, ...]

// Detect recurring transactions
const recurring = await transactionsAPI.detectRecurring(3); // min 3 occurrences
// Returns: {
//   recurring: [ ...recurring transactions ],
//   total_count: 10
// }

// Upload CSV
const result = await transactionsAPI.uploadCSV(file, accountId);
// Returns: { inserted_count, skipped_count, account_id }

// Update transaction note
await transactionsAPI.updateNote(transactionId, 'My custom note');

// Update transaction category
await transactionsAPI.updateCategory(transactionId, 'Groceries');
```

### Dashboard API

```javascript
import { dashboardAPI } from '../services/api';

// Get current month stats
const stats = await dashboardAPI.getStats();
// Returns: {
//   total_balance: 1234.56,
//   total_expenses: 2345.67,
//   total_income: 3580.23,
//   savings: 1234.56,
//   savings_rate: 34.5,
//   transaction_count: 123,
//   account_count: 2,
//   top_category: 'Groceries',
//   top_category_amount: 456.78
// }

// Get stats for specific period
const periodStats = await dashboardAPI.getStatsPeriod(6); // last 6 months
```

### AI API

```javascript
import { aiAPI } from '../services/api';

// Categorize merchant
const categorization = await aiAPI.categorizeMerchant(
  'amazon',
  ['AMAZON.COM*123ABC', 'AMAZON PRIME']
);
// Returns: {
//   merchant_key: 'amazon',
//   category: 'Shopping',
//   note: 'Online retail purchases',
//   explanation: '...'
// }

// Get AI insights
const insights = await aiAPI.getInsights({
  date_range: 'last_3_months',
  category: ['Groceries', 'Dining']
});
// Returns: {
//   insights: ['You spent 20% more on dining this month...', ...]
// }
```

## Data Transformation

The API client automatically transforms backend data to frontend format:

### Backend Transaction Format
```javascript
{
  id: 1,
  date: "2024-01-15",
  description_raw: "AMAZON.COM*123ABC",
  merchant_key: "amazon",
  amount: -50.00,
  currency: "CAD",
  category: "Shopping",
  category_source: "ai",
  note_user: "Birthday gift",
  account_id: 1,
  user_id: 1,
  created_at: "2024-01-15T10:30:00"
}
```

### Frontend Transaction Format (after transformation)
```javascript
{
  id: 1,
  date: "2024-01-15",
  descriptionRaw: "AMAZON.COM*123ABC",
  merchant: "amazon",
  amount: -50.00,
  currency: "CAD",
  category: "Shopping",
  categorySource: "ai",
  noteUser: "Birthday gift",
  accountId: 1,
  userId: 1,
  createdAt: "2024-01-15T10:30:00"
}
```

Use `transformTransaction(transaction)` to convert backend format to frontend format.

## Error Handling

All API calls return promises. Handle errors appropriately:

```javascript
try {
  const response = await transactionsAPI.getView(params);
  // Handle success
} catch (error) {
  if (error.response) {
    // Backend returned error
    console.error('API Error:', error.response.status, error.response.data);
  } else if (error.request) {
    // No response received
    console.error('Network Error:', error.message);
  } else {
    // Request setup error
    console.error('Error:', error.message);
  }
}
```

## Authentication

Currently, the API client uses session-based authentication with `withCredentials: true`. If you need to implement JWT authentication:

1. Uncomment the token handling in `src/services/api.js`
2. Store tokens in localStorage after login
3. The interceptor will automatically add the Authorization header

## Next Steps

1. ✅ API client created
2. ✅ Environment configured
3. 🔄 Integrate TransactionsPage with API
4. 🔄 Integrate DashboardPage with API
5. 🔄 Integrate UploadPage with API
6. 🔄 Integrate RecurringPage with API
7. ⏳ Add error handling and loading states
8. ⏳ Add authentication flow
