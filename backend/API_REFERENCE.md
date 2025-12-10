# API Reference

Complete reference for the Personal Finance Intelligence API.

Base URL: `http://localhost:8000`

## Authentication

Currently in single-user mode (no authentication required).
All requests use `user_id=1` by default.

---

## Health & Status

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### GET /

Root endpoint with API information.

**Response:**
```json
{
  "message": "Personal Finance Intelligence API",
  "docs": "/docs",
  "version": "1.0.0"
}
```

---

## Accounts

### GET /api/v1/accounts

Get all accounts for the current user.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "MasterCard •••• 1712",
    "institution": "RBC",
    "account_type": "MasterCard",
    "account_number_last4": "1712",
    "currency": "CAD",
    "created_at": "2025-12-02T10:00:00"
  }
]
```

### GET /api/v1/accounts/{account_id}

Get a specific account.

**Parameters:**
- `account_id` (path): Account ID

**Response:** Same as single account object above

**Errors:**
- `404`: Account not found

### POST /api/v1/accounts

Create a new account.

**Request Body:**
```json
{
  "name": "MasterCard •••• 1712",
  "institution": "RBC",
  "account_type": "MasterCard",
  "account_number_last4": "1712",
  "currency": "CAD"
}
```

**Response:** Created account object

---

## Transactions

### POST /api/v1/transactions/upload_csv

Upload and parse a CSV file containing transactions.

**Request:**
- Content-Type: `multipart/form-data`
- `file`: CSV file
- `account_id` (optional): Account ID to associate transactions with

**Response:**
```json
{
  "inserted_count": 120,
  "skipped_count": 3,
  "account_id": 1
}
```

**Errors:**
- `400`: Invalid CSV format or parsing error

### GET /api/v1/transactions/view

Get filtered transactions with aggregates (Excel-style filtering).

**Query Parameters:**
- `account_id` (int, optional): Filter by account
- `start_date` (date, optional): Start date (YYYY-MM-DD)
- `end_date` (date, optional): End date (YYYY-MM-DD)
- `category` (string, optional): Category name (comma-separated for multiple)
- `merchant_query` (string, optional): Search term for merchant/description
- `min_amount` (float, optional): Minimum amount
- `max_amount` (float, optional): Maximum amount
- `page` (int, default=1): Page number
- `page_size` (int, default=50): Results per page

**Response:**
```json
{
  "filters": {
    "account_id": 1,
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "category": "Groceries,Transport",
    "merchant_query": null,
    "min_amount": null,
    "max_amount": null
  },
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 432
  },
  "rows": [
    {
      "id": 123,
      "account_id": 1,
      "user_id": 1,
      "date": "2025-10-13",
      "description_raw": "MCDONALD'S #41147 OSHAWA",
      "merchant_key": "MCDONALDS",
      "amount": -20.88,
      "currency": "CAD",
      "category": "Uncategorized",
      "category_source": "uncategorized",
      "note_user": null,
      "created_at": "2025-12-02T10:30:00"
    }
  ],
  "aggregates": {
    "total_spent": -1234.56,
    "total_income": 3000.00,
    "by_category": {
      "Groceries": -400.12,
      "Transport": -120.50
    },
    "by_day": [
      {
        "date": "2025-10-01",
        "net": -45.00
      },
      {
        "date": "2025-10-02",
        "net": -23.50
      }
    ]
  }
}
```

### PATCH /api/v1/transactions/{transaction_id}/note

Update the user note for a transaction.

**Parameters:**
- `transaction_id` (path): Transaction ID

**Request Body:**
```json
{
  "note_user": "Lunch with Sarah"
}
```

**Response:** Updated transaction object

**Errors:**
- `404`: Transaction not found

### PATCH /api/v1/transactions/{transaction_id}/category

Update the category for a transaction.

**Parameters:**
- `transaction_id` (path): Transaction ID

**Request Body:**
```json
{
  "category": "Eating Out"
}
```

**Response:** Updated transaction object (with `category_source` set to "user")

**Errors:**
- `404`: Transaction not found

---

## AI Features

### POST /api/v1/ai/categorize_merchant

Categorize a merchant using AI (with caching).

**Request Body:**
```json
{
  "merchant_key": "MCDONALDS",
  "sample_descriptions": [
    "MCDONALD'S #41147 OSHAWA",
    "MCDONALD'S #12345 TORONTO"
  ]
}
```

**Response:**
```json
{
  "merchant_key": "MCDONALDS",
  "category": "Eating Out",
  "note": "Lunch – McDonald's",
  "explanation": "McDonald's is a fast food restaurant, so these are eating-out expenses."
}
```

**Notes:**
- Results are cached per merchant_key
- Automatically updates all uncategorized transactions for this merchant
- Returns stub data if no OpenRouter API key is configured

**Errors:**
- `500`: AI service error

### POST /api/v1/ai/insights

Generate AI-powered insights based on filtered transactions.

**Request Body:**
```json
{
  "account_id": 1,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "category": ["Groceries", "Transport"],
  "merchant_query": null,
  "min_amount": null,
  "max_amount": null
}
```

**Response:**
```json
{
  "insights": [
    "Your total spending for this period was $1234.56, mostly in Groceries and Transport.",
    "Your Transport spending was lower than usual compared to the previous period.",
    "You have several recurring charges from Streaming services.",
    "Consider reviewing your Subscription category for potential savings."
  ]
}
```

**Notes:**
- Uses same filtering logic as `/transactions/view`
- Returns stub insights if no OpenRouter API key is configured

**Errors:**
- `500`: AI service error

---

## Data Types

### Transaction Categories

Supported categories:
- `Groceries`
- `Rent`
- `Transport`
- `Eating Out`
- `Shopping`
- `Subscription`
- `Utilities`
- `Income`
- `Other`

### Category Source

How a transaction was categorized:
- `uncategorized`: Not yet categorized
- `rule`: Categorized by rule
- `ai`: Categorized by AI
- `user`: Manually categorized by user

### Date Format

All dates use ISO 8601 format: `YYYY-MM-DD`

Example: `2025-10-13`

### Amount Convention

- **Negative values**: Spending/expenses (e.g., `-20.88`)
- **Positive values**: Income/credits (e.g., `2500.00`)

---

## CSV Format

The API expects RBC-style CSV with these columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| Account Type | string | Yes | Type of account (e.g., "MasterCard") |
| Account Number | string | Yes | Full account number |
| Transaction Date | string | Yes | Date in MM/DD/YYYY format |
| Cheque Number | string | No | Cheque number (if applicable) |
| Description 1 | string | Yes | Primary description |
| Description 2 | string | No | Secondary description |
| CAD$ | float | * | Amount in CAD |
| USD$ | float | * | Amount in USD |

\* At least one of CAD$ or USD$ must be present

**Example:**
```csv
Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$,USD$
MasterCard,5415901952021712,10/12/2025,,TST-Nest Uxbridge,, -5.09,
MasterCard,5415901952021712,10/13/2025,,MCDONALD'S #41147 OSHAWA,, -20.88,
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found
- `500`: Internal Server Error

---

## Rate Limiting

Currently no rate limiting implemented.

For production, consider implementing rate limiting based on:
- IP address
- User ID (when auth is added)
- Endpoint type

---

## CORS

Currently configured to allow all origins (`*`).

For production, update CORS settings in `app/main.py` to allow only your frontend domain.

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- JSON: http://localhost:8000/api/v1/openapi.json
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Examples

### Complete Workflow

1. **Upload CSV:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
     -F "file=@statement.csv"
   ```

2. **View transactions:**
   ```bash
   curl "http://localhost:8000/api/v1/transactions/view?start_date=2025-10-01&end_date=2025-10-31"
   ```

3. **Categorize merchant:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/categorize_merchant" \
     -H "Content-Type: application/json" \
     -d '{"merchant_key":"MCDONALDS","sample_descriptions":["MCDONALD'\''S OSHAWA"]}'
   ```

4. **Update note:**
   ```bash
   curl -X PATCH "http://localhost:8000/api/v1/transactions/1/note" \
     -H "Content-Type: application/json" \
     -d '{"note_user":"Lunch meeting"}'
   ```

5. **Get insights:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/ai/insights" \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2025-10-01","end_date":"2025-10-31"}'
   ```

---

## Support

- Interactive API Explorer: http://localhost:8000/docs
- GitHub: [Your repository URL]
- Documentation: See [README.md](README.md)

---

Built with FastAPI 🚀
