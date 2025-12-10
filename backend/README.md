# Personal Finance Intelligence API

A FastAPI backend for managing and analyzing personal financial transactions with AI-powered categorization and insights.

## Features

- **CSV Import**: Upload bank statements (RBC format) and automatically parse transactions
- **Transaction Management**: Filter, search, and categorize transactions
- **AI Categorization**: Automatically categorize merchants using AI (OpenRouter)
- **AI Insights**: Generate narrative insights about spending patterns
- **Merchant Caching**: Cache AI categorization results for better performance
- **Aggregated Analytics**: Compute spending by category, day, and more
- **Excel-style Filtering**: All aggregates computed on filtered subset of data

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Database**: SQLite (easily switchable to PostgreSQL)
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **AI Provider**: OpenRouter (supports Claude, GPT-4, and more)
- **CSV Parsing**: Pandas

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   └── config.py          # Configuration settings
│   ├── db/
│   │   ├── session.py         # Database session management
│   │   └── base.py            # Base model imports
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── merchant_cache.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── merchant_cache.py
│   ├── api/
│   │   ├── deps.py           # Dependency injection
│   │   └── v1/
│   │       ├── accounts.py   # Account endpoints
│   │       ├── transactions.py  # Transaction endpoints
│   │       └── ai.py         # AI endpoints
│   └── services/             # Business logic
│       ├── csv_import.py
│       ├── categorization.py
│       ├── insights.py
│       └── merchant_normalization.py
├── alembic/                  # Database migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. **Clone the repository and navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenRouter API key (optional but recommended for AI features):
   ```env
   DATABASE_URL=sqlite:///./finance.db
   OPENROUTER_API_KEY=your_api_key_here
   OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
   ```

   Get your API key from: https://openrouter.ai/

5. **Initialize the database**:
   The database will be automatically created when you first run the application.
   Tables are created using SQLAlchemy's `create_all()` method.

## Running the Application

### Development Mode

```bash
# From the backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use Python directly:

```bash
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Database Migrations (Optional)

While the app creates tables automatically, you can use Alembic for migrations:

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## API Endpoints

### Health Check

```bash
GET /health
```

### Accounts

```bash
# Get all accounts
GET /api/v1/accounts

# Get specific account
GET /api/v1/accounts/{account_id}

# Create account
POST /api/v1/accounts
Content-Type: application/json
{
  "name": "MasterCard •••• 1712",
  "institution": "RBC",
  "account_type": "MasterCard",
  "account_number_last4": "1712",
  "currency": "CAD"
}
```

### Transactions

```bash
# Upload CSV
POST /api/v1/transactions/upload_csv
Content-Type: multipart/form-data
file: @statement.csv
account_id: 1 (optional)

# Get filtered transactions with aggregates
GET /api/v1/transactions/view?account_id=1&start_date=2025-10-01&end_date=2025-10-31&page=1&page_size=50

# Update transaction note
PATCH /api/v1/transactions/{transaction_id}/note
Content-Type: application/json
{
  "note_user": "Lunch with Sarah"
}

# Update transaction category
PATCH /api/v1/transactions/{transaction_id}/category
Content-Type: application/json
{
  "category": "Eating Out"
}
```

### AI Features

```bash
# Categorize merchant with AI
POST /api/v1/ai/categorize_merchant
Content-Type: application/json
{
  "merchant_key": "MCDONALDS",
  "sample_descriptions": [
    "MCDONALD'S #41147 OSHAWA",
    "MCDONALD'S #12345 TORONTO"
  ]
}

# Generate insights
POST /api/v1/ai/insights
Content-Type: application/json
{
  "account_id": 1,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31",
  "category": ["Groceries", "Transport"]
}
```

## Example Usage with cURL

### 1. Upload a CSV file

```bash
curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@statement.csv"
```

Response:
```json
{
  "inserted_count": 120,
  "skipped_count": 3,
  "account_id": 1
}
```

### 2. Get filtered transactions

```bash
curl -X GET "http://localhost:8000/api/v1/transactions/view?start_date=2025-10-01&end_date=2025-10-31&page=1&page_size=10"
```

Response:
```json
{
  "filters": {
    "account_id": null,
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "category": null,
    "merchant_query": null,
    "min_amount": null,
    "max_amount": null
  },
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_count": 120
  },
  "rows": [
    {
      "id": 1,
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
      {"date": "2025-10-01", "net": -45.00},
      {"date": "2025-10-02", "net": -23.50}
    ]
  }
}
```

### 3. Categorize a merchant with AI

```bash
curl -X POST "http://localhost:8000/api/v1/ai/categorize_merchant" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_key": "MCDONALDS",
    "sample_descriptions": [
      "MCDONALD'\''S #41147 OSHAWA",
      "MCDONALD'\''S #12345 TORONTO"
    ]
  }'
```

Response:
```json
{
  "merchant_key": "MCDONALDS",
  "category": "Eating Out",
  "note": "Lunch – McDonald's",
  "explanation": "McDonald's is a fast food restaurant, so these are eating-out expenses."
}
```

### 4. Generate AI insights

```bash
curl -X POST "http://localhost:8000/api/v1/ai/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-31"
  }'
```

Response:
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

### 5. Update transaction note

```bash
curl -X PATCH "http://localhost:8000/api/v1/transactions/1/note" \
  -H "Content-Type: application/json" \
  -d '{"note_user": "Lunch with Sarah"}'
```

### 6. Update transaction category

```bash
curl -X PATCH "http://localhost:8000/api/v1/transactions/1/category" \
  -H "Content-Type: application/json" \
  -d '{"category": "Eating Out"}'
```

## CSV Format

The backend expects RBC-style CSV with the following columns:

```csv
Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$,USD$
MasterCard,5415901952021712,10/12/2025,,TST-Nest Uxbridge,, -5.09,
MasterCard,5415901952021712,10/13/2025,,MCDONALD'S #41147 OSHAWA,, -20.88,
```

Required columns:
- `Account Type`: Type of account (e.g., "MasterCard")
- `Account Number`: Full account number
- `Transaction Date`: Date in MM/DD/YYYY format
- `Description 1`: Primary description
- `Description 2`: Secondary description (optional)
- `CAD$`: Amount in CAD (negative for spending, positive for income)
- `USD$`: Amount in USD (if CAD$ is empty)

## Supported Categories

- Groceries
- Rent
- Transport
- Eating Out
- Shopping
- Subscription
- Utilities
- Income
- Other

## AI Integration

The backend integrates with OpenRouter to provide:

1. **Merchant Categorization**: Automatically categorizes unknown merchants
2. **Smart Caching**: Caches AI results per merchant to minimize API calls
3. **Bulk Updates**: Automatically updates all uncategorized transactions for a merchant
4. **Insights Generation**: Provides narrative insights about spending patterns

### Without API Key

If no OpenRouter API key is provided, the app will:
- Still work for all non-AI features
- Return stub data for AI endpoints
- Display helpful messages to connect an API key

## Migration to PostgreSQL

To switch from SQLite to PostgreSQL:

1. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/finance_db
   ```

2. Remove SQLite-specific connection args in [app/db/session.py](app/db/session.py:8-11):
   ```python
   engine = create_engine(
       settings.DATABASE_URL,
       echo=False
   )
   ```

3. Run migrations:
   ```bash
   alembic upgrade head
   ```

## Testing

You can test the API using:

1. **Interactive Docs**: http://localhost:8000/docs
2. **cURL**: See examples above
3. **Postman**: Import the OpenAPI spec from `/api/v1/openapi.json`
4. **Python requests**:
   ```python
   import requests

   response = requests.get("http://localhost:8000/api/v1/accounts")
   print(response.json())
   ```

## Troubleshooting

### Database Errors

If you encounter database errors:
```bash
# Delete the database and start fresh
rm finance.db
# Restart the application - it will recreate the database
```

### Import Errors

If you see import errors:
```bash
# Make sure you're in the backend directory
cd backend
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
# Reinstall dependencies
pip install -r requirements.txt
```

### OpenRouter API Errors

If AI features aren't working:
- Check your API key in `.env`
- Verify you have credits at https://openrouter.ai/
- Check the model name is correct

## Security Notes

**For Production**:

1. Update CORS settings in [app/main.py](app/main.py:22-28) to allow only your frontend domain
2. Add authentication/authorization middleware
3. Use environment variables for all secrets
4. Enable HTTPS
5. Set up proper database backups
6. Use PostgreSQL instead of SQLite
7. Add rate limiting
8. Validate and sanitize all user inputs

## License

MIT

## Support

For issues and questions:
- Check the [Interactive API Docs](http://localhost:8000/docs)
- Review the code in the `app/` directory
- Check OpenRouter documentation: https://openrouter.ai/docs

---

Built with FastAPI, SQLAlchemy, and OpenRouter 🚀
