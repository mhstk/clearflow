# Quick Start Guide

Get the Personal Finance Intelligence API running in 5 minutes!

## 1. Setup Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenRouter API key (optional)
# Get one from: https://openrouter.ai/
```

## 3. Start the Server

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
uvicorn app.main:app --reload
```

The server will start at: http://localhost:8000

## 4. Test the API

Open your browser and visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Or run the test script:

```bash
# In a new terminal (keep the server running)
python test_api.py
```

## 5. Upload Sample Data

### Using the Interactive Docs (Easiest)

1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/transactions/upload_csv`
3. Click "Try it out"
4. Upload the `sample_statement.csv` file
5. Click "Execute"

### Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_statement.csv"
```

## 6. View Your Data

### Get Transactions

```bash
curl "http://localhost:8000/api/v1/transactions/view?page_size=10"
```

Or visit: http://localhost:8000/docs and try the GET endpoints

## 7. Try AI Features

### Categorize a Merchant

```bash
curl -X POST "http://localhost:8000/api/v1/ai/categorize_merchant" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_key": "MCDONALDS",
    "sample_descriptions": ["MCDONALD'\''S #41147 OSHAWA"]
  }'
```

### Generate Insights

```bash
curl -X POST "http://localhost:8000/api/v1/ai/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-31"
  }'
```

## Common Commands

```bash
# Start server
python run.py

# Run tests
python test_api.py

# View all transactions
curl "http://localhost:8000/api/v1/transactions/view"

# Get accounts
curl "http://localhost:8000/api/v1/accounts"

# Health check
curl "http://localhost:8000/health"
```

## Next Steps

1. **Upload your real bank statement** (CSV format)
2. **Explore the API docs** at http://localhost:8000/docs
3. **Try filtering transactions** by date, category, or merchant
4. **Use AI to categorize** your transactions
5. **Get spending insights** with the AI insights endpoint

## Troubleshooting

### Port already in use?

Change the port in `run.py`:
```python
uvicorn.run(..., port=8001)
```

### Import errors?

Make sure virtual environment is activated:
```bash
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Database issues?

Delete and recreate:
```bash
rm finance.db
python run.py  # Will recreate automatically
```

## Support

- Check the [README.md](README.md) for detailed documentation
- Visit http://localhost:8000/docs for API reference
- Review the code in the `app/` directory

Happy analyzing! 📊
