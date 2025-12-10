# API Endpoints - Complete Reference

All new endpoints and improvements for the Personal Finance Intelligence API.

Base URL: `http://localhost:8000`

---

## 🆕 New Endpoints

### 1. GET /api/v1/transactions/{id}

Get a single transaction by ID.

**Request:**
```bash
curl "http://localhost:8000/api/v1/transactions/123"
```

**Response:**
```json
{
  "id": 123,
  "account_id": 1,
  "user_id": 1,
  "date": "2025-10-13",
  "description_raw": "MCDONALD'S #41147 OSHAWA",
  "merchant_key": "MCDONALDS",
  "amount": -20.88,
  "currency": "CAD",
  "category": "Eating Out",
  "category_source": "ai",
  "note_user": "Lunch meeting",
  "created_at": "2025-12-02T10:30:00"
}
```

**Error Response (404):**
```json
{
  "detail": "Transaction not found"
}
```

---

### 2. GET /api/v1/transactions/categories/list

Get all categories used in user's transactions with statistics.

**Request:**
```bash
curl "http://localhost:8000/api/v1/transactions/categories/list"
```

**Response:**
```json
[
  {
    "category": "Groceries",
    "count": 45,
    "total_amount": -1234.56
  },
  {
    "category": "Transport",
    "count": 23,
    "total_amount": -456.78
  },
  {
    "category": "Eating Out",
    "count": 18,
    "total_amount": -345.67
  }
]
```

**Use Cases:**
- Populate category filter dropdown
- Show category breakdown
- Display spending by category

---

### 3. GET /api/v1/transactions/recurring/detect

Detect recurring transactions based on merchant patterns.

**Parameters:**
- `min_occurrences` (int, optional): Minimum transactions to consider as recurring (default: 3)

**Request:**
```bash
curl "http://localhost:8000/api/v1/transactions/recurring/detect?min_occurrences=3"
```

**Response:**
```json
{
  "recurring": [
    {
      "merchant_key": "NETFLIX",
      "merchant_name": "NETFLIX.COM",
      "category": "Subscription",
      "average_amount": -16.99,
      "frequency": "monthly",
      "transaction_count": 6,
      "last_transaction_date": "2025-11-15",
      "next_expected_date": "2025-12-15",
      "sample_transactions": [123, 456, 789]
    },
    {
      "merchant_key": "SPOTIFY",
      "merchant_name": "SPOTIFY",
      "category": "Subscription",
      "average_amount": -10.99,
      "frequency": "monthly",
      "transaction_count": 8,
      "last_transaction_date": "2025-11-20",
      "next_expected_date": "2025-12-20",
      "sample_transactions": [234, 567, 890]
    }
  ],
  "total_count": 2
}
```

**Frequency Values:**
- `weekly`: Transactions every ~7 days
- `monthly`: Transactions every ~30 days
- `quarterly`: Transactions every ~90 days
- `irregular`: Inconsistent pattern
- `unknown`: Not enough data

**Use Cases:**
- Recurring subscriptions page
- Budget planning
- Subscription management
- Identify regular expenses

---

### 4. GET /api/v1/dashboard/stats

Get dashboard statistics for the current month.

**Request:**
```bash
curl "http://localhost:8000/api/v1/dashboard/stats"
```

**Response:**
```json
{
  "total_balance": 1265.44,
  "total_expenses": 2734.56,
  "total_income": 4000.00,
  "savings": 1265.44,
  "savings_rate": 31.64,
  "transaction_count": 87,
  "account_count": 2,
  "top_category": "Groceries",
  "top_category_amount": 876.54
}
```

**Field Descriptions:**
- `total_balance`: Net balance (income - expenses) for current month
- `total_expenses`: Total spending (absolute value)
- `total_income`: Total income
- `savings`: Same as total_balance
- `savings_rate`: Percentage of income saved
- `transaction_count`: Number of transactions this month
- `account_count`: Total number of accounts
- `top_category`: Category with most spending
- `top_category_amount`: Amount spent in top category

---

### 5. GET /api/v1/dashboard/stats/period

Get dashboard statistics for a custom period.

**Parameters:**
- `months` (int, optional): Number of months to look back (default: 1)

**Request:**
```bash
# Last 3 months
curl "http://localhost:8000/api/v1/dashboard/stats/period?months=3"

# Last 6 months
curl "http://localhost:8000/api/v1/dashboard/stats/period?months=6"

# Last year
curl "http://localhost:8000/api/v1/dashboard/stats/period?months=12"
```

**Response:** Same format as `/dashboard/stats`

---

## ✨ Improved Endpoints

### GET /api/v1/transactions/view (Enhanced)

**New Features:**
1. `date_range` enum support
2. Multiple categories as array
3. by_day in descending order

**New Parameters:**
- `date_range`: Preset date ranges (optional)
  - `this_month`
  - `last_month`
  - `last_3_months`
  - `last_6_months`
  - `this_year`
  - `all_time`

- `category`: Now accepts multiple values as array

**Example 1: Using date_range**
```bash
# This month's transactions
curl "http://localhost:8000/api/v1/transactions/view?date_range=this_month"

# Last 3 months
curl "http://localhost:8000/api/v1/transactions/view?date_range=last_3_months"

# This year
curl "http://localhost:8000/api/v1/transactions/view?date_range=this_year"
```

**Example 2: Multiple categories**
```bash
# Filter by multiple categories
curl "http://localhost:8000/api/v1/transactions/view?category=Groceries&category=Transport&category=Utilities"
```

**Example 3: Combining filters**
```bash
curl "http://localhost:8000/api/v1/transactions/view?date_range=last_month&category=Groceries&category=Eating%20Out&page_size=20"
```

**Response Changes:**
```json
{
  "filters": {
    "account_id": null,
    "start_date": "2025-11-01",
    "end_date": "2025-11-30",
    "date_range": "last_month",
    "category": ["Groceries", "Eating Out"],
    "merchant_query": null,
    "min_amount": null,
    "max_amount": null
  },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 45
  },
  "rows": [...],
  "aggregates": {
    "total_spent": -1234.56,
    "total_income": 0.0,
    "by_category": {
      "Groceries": -876.45,
      "Eating Out": -358.11
    },
    "by_day": [
      {"date": "2025-11-30", "net": -45.67},
      {"date": "2025-11-29", "net": -23.45},
      {"date": "2025-11-28", "net": -67.89}
    ]
  }
}
```

**Note:** `by_day` is now in **descending order** (most recent first).

---

## 📋 Complete Endpoint List

### Transactions (9 endpoints)
1. `POST /api/v1/transactions/upload_csv` - Upload CSV file
2. `GET /api/v1/transactions/view` - Filtered view with aggregates
3. `GET /api/v1/transactions/{id}` - Get single transaction ⭐ NEW
4. `GET /api/v1/transactions/categories/list` - List all categories ⭐ NEW
5. `GET /api/v1/transactions/recurring/detect` - Detect recurring ⭐ NEW
6. `PATCH /api/v1/transactions/{id}/note` - Update note
7. `PATCH /api/v1/transactions/{id}/category` - Update category

### Dashboard (2 endpoints) ⭐ NEW
8. `GET /api/v1/dashboard/stats` - Current month stats
9. `GET /api/v1/dashboard/stats/period` - Custom period stats

### Accounts (3 endpoints)
10. `GET /api/v1/accounts` - List accounts
11. `GET /api/v1/accounts/{id}` - Get account
12. `POST /api/v1/accounts` - Create account

### AI (2 endpoints)
13. `POST /api/v1/ai/categorize_merchant` - Categorize with AI
14. `POST /api/v1/ai/insights` - Generate insights

### System (2 endpoints)
15. `GET /` - API info
16. `GET /health` - Health check

**Total: 16 endpoints** (was 12, added 4 new + 1 new section)

---

## 🎯 Frontend Integration Examples

### Dashboard Page

```javascript
// Get dashboard stats
const stats = await fetch('/api/v1/dashboard/stats').then(r => r.json());

// Display:
// - Total Balance: ${stats.total_balance}
// - Income: ${stats.total_income}
// - Expenses: ${stats.total_expenses}
// - Savings Rate: ${stats.savings_rate}%
// - Top Spending: ${stats.top_category} (${stats.top_category_amount})
```

### Transactions Page with Filters

```javascript
// Build filter URL
const params = new URLSearchParams({
  date_range: 'last_3_months',
  page_size: 50,
  page: 1
});

// Add category filters
['Groceries', 'Transport'].forEach(cat => {
  params.append('category', cat);
});

const data = await fetch(`/api/v1/transactions/view?${params}`)
  .then(r => r.json());

// Use data.rows for table
// Use data.aggregates for charts
```

### Category Filter Dropdown

```javascript
// Get all categories
const categories = await fetch('/api/v1/transactions/categories/list')
  .then(r => r.json());

// Populate dropdown
categories.forEach(cat => {
  console.log(`${cat.category}: ${cat.count} transactions, $${cat.total_amount}`);
});
```

### Recurring Subscriptions Page

```javascript
// Detect recurring transactions
const recurring = await fetch('/api/v1/transactions/recurring/detect?min_occurrences=3')
  .then(r => r.json());

// Display each subscription
recurring.recurring.forEach(sub => {
  console.log(`${sub.merchant_name}: ${sub.average_amount} ${sub.frequency}`);
  console.log(`Next expected: ${sub.next_expected_date}`);
});
```

---

## 🔍 Query Parameter Formats

### Date Formats

**ISO 8601 format:** `YYYY-MM-DD`

```bash
?start_date=2025-01-01&end_date=2025-12-31
```

### Date Range Enum

```bash
?date_range=this_month
?date_range=last_month
?date_range=last_3_months
?date_range=last_6_months
?date_range=this_year
?date_range=all_time
```

### Multiple Categories

```bash
# Method 1: Multiple query params (recommended)
?category=Groceries&category=Transport&category=Utilities

# Method 2: Array notation (also supported)
?category[]=Groceries&category[]=Transport
```

### Pagination

```bash
?page=1&page_size=50
```

---

## 🚨 Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (transaction, account, etc.)
- `422` - Validation Error (Pydantic)
- `500` - Server Error

### Example Error Response

```bash
curl "http://localhost:8000/api/v1/transactions/99999"
```

```json
{
  "detail": "Transaction not found"
}
```

---

## 📊 Data Type Reference

### DateRangeEnum

```python
this_month      # Current month to today
last_month      # Previous complete month
last_3_months   # Last 90 days
last_6_months   # Last 180 days
this_year       # Jan 1 to today
all_time        # All transactions
```

### Frequency (Recurring)

```python
weekly      # ~7 day intervals
monthly     # ~30 day intervals
quarterly   # ~90 day intervals
irregular   # Inconsistent pattern
unknown     # Not enough data
```

### Category Source

```python
uncategorized   # Not yet categorized
rule            # Categorized by rule
ai              # Categorized by AI
user            # Manually categorized
```

---

## 🔧 Testing New Endpoints

### Test Script

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Get dashboard stats
stats = requests.get(f"{BASE_URL}/dashboard/stats").json()
print(f"Balance: ${stats['total_balance']}")

# 2. Get categories
categories = requests.get(f"{BASE_URL}/transactions/categories/list").json()
print(f"Categories: {len(categories)}")

# 3. Detect recurring
recurring = requests.get(f"{BASE_URL}/transactions/recurring/detect").json()
print(f"Recurring: {recurring['total_count']}")

# 4. Get transactions with date_range
transactions = requests.get(
    f"{BASE_URL}/transactions/view",
    params={"date_range": "last_month"}
).json()
print(f"Transactions: {transactions['pagination']['total_count']}")

# 5. Filter by multiple categories
transactions = requests.get(
    f"{BASE_URL}/transactions/view",
    params={
        "category": ["Groceries", "Transport"],
        "date_range": "last_3_months"
    }
).json()
print(f"Filtered: {transactions['pagination']['total_count']}")
```

---

## 🎨 Frontend Component Mapping

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| Dashboard Cards | `/dashboard/stats` | Show balance, income, expenses |
| Dashboard Charts | `/transactions/view` | Historical spending charts |
| Category Filter | `/transactions/categories/list` | Populate filter dropdown |
| Transactions Table | `/transactions/view` | Display transactions |
| Transaction Detail | `/transactions/{id}` | Show single transaction |
| Recurring Page | `/transactions/recurring/detect` | List subscriptions |
| Date Range Picker | `/transactions/view?date_range=...` | Quick date filters |

---

## 📖 Migration Guide

### Old vs New

**Before (comma-separated categories):**
```bash
?category=Groceries,Transport
```

**After (array notation):**
```bash
?category=Groceries&category=Transport
```

**Both are supported** but array notation is recommended for clarity.

---

## ✅ Summary of Improvements

1. ✅ Added `/transactions/{id}` - Get single transaction
2. ✅ Added `/transactions/categories/list` - List all categories
3. ✅ Added `/transactions/recurring/detect` - Detect recurring
4. ✅ Added `/dashboard/stats` - Dashboard metrics
5. ✅ Added `/dashboard/stats/period` - Custom period stats
6. ✅ Added `date_range` enum support
7. ✅ Improved category filtering (array support)
8. ✅ Fixed `by_day` sorting (descending order)
9. ✅ Added comprehensive error handling
10. ✅ Added detailed documentation

---

Built with FastAPI 🚀
