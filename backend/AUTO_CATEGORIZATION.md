# AI Auto-Categorization Feature

Complete guide to the AI-powered transaction categorization system.

## Overview

The auto-categorization feature uses Amazon Nova 2 Lite (via OpenRouter) to automatically categorize transactions based on merchant names and amounts. It includes intelligent caching, batch processing, and validation.

## Features

✅ **Batch Processing** - Categorize multiple transactions at once
✅ **Merchant Caching** - Avoid redundant AI calls
✅ **Category Validation** - Ensures only valid categories are assigned
✅ **Confidence Scores** - High/Medium/Low confidence ratings
✅ **Auto-Apply** - Optional automatic application to database
✅ **CSV Integration** - Auto-categorize on upload
✅ **Customizable Prompts** - Easy to modify templates

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install the new `openai==1.58.1` library.

### 2. Configure API Key

Add your OpenRouter API key to `.env`:

```env
OPENROUTER_API_KEY=your_key_here
```

Get a free API key at: https://openrouter.ai/

### 3. Test the Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/ai/categorize_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_ids": [1, 2, 3],
    "auto_apply": true
  }'
```

---

## API Endpoints

### POST /api/v1/ai/categorize_batch

Categorize multiple transactions at once.

**Request:**
```json
{
  "transaction_ids": [1, 2, 3, 4, 5],
  "auto_apply": true
}
```

**Parameters:**
- `transaction_ids` (required): Array of transaction IDs
- `auto_apply` (optional): Whether to save categories to database (default: true)

**Response:**
```json
{
  "results": [
    {
      "transaction_id": 1,
      "category": "Groceries",
      "note": "Weekly shopping at Loblaws",
      "confidence": "high",
      "applied": true,
      "error": null
    },
    {
      "transaction_id": 2,
      "category": "Eating Out",
      "note": "Fast food lunch",
      "confidence": "high",
      "applied": true,
      "error": null
    }
  ],
  "total_processed": 5,
  "successful": 5,
  "failed": 0
}
```

**Features:**
- Uses cached results when available (instant)
- Validates categories against allowed list
- Provides confidence scores
- Handles errors per transaction

---

### POST /api/v1/transactions/upload_csv (Enhanced)

Now supports auto-categorization on upload!

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
  -F "file=@statement.csv" \
  -F "auto_categorize=true"
```

**Parameters:**
- `file` (required): CSV file
- `account_id` (optional): Account ID
- `auto_categorize` (optional): Auto-categorize after upload (default: false)

**Response:**
```json
{
  "inserted_count": 20,
  "skipped_count": 0,
  "account_id": 1
}
```

When `auto_categorize=true`, all uploaded transactions are automatically categorized using AI.

---

## How It Works

### 1. Merchant Cache

The system maintains a cache of merchant categorizations:

```python
{
  "MCDONALDS": {
    "category": "Eating Out",
    "note": "Fast food",
    "confidence": "high"
  }
}
```

When categorizing a transaction, it first checks the cache. If found, it uses the cached result instantly (no AI call needed).

### 2. Batch AI Call

For uncached merchants, the system:

1. **Collects** all uncached transactions
2. **Builds** a structured prompt with merchant names and amounts
3. **Calls** OpenRouter API (Amazon Nova 2 Lite)
4. **Parses** JSON response
5. **Validates** categories against allowed list
6. **Caches** results for future use
7. **Applies** categories to database (if auto_apply=true)

### 3. Category Validation

After receiving AI response, categories are validated:

```python
VALID_CATEGORIES = [
    "Groceries",
    "Rent",
    "Transport",
    "Eating Out",
    "Shopping",
    "Subscription",
    "Utilities",
    "Income",
    "Other",
    "Uncategorized"
]
```

If AI suggests an invalid category, it defaults to "Uncategorized".

---

## Customizing Prompts

Prompts are stored in easily editable files:

### Location
```
backend/app/prompts/categorization.py
```

### Batch Prompt

```python
def get_batch_categorization_prompt(
    transactions: List[Dict],
    available_categories: List[str]
) -> str:
    # Modify this function to customize the prompt
    pass
```

### Example Customizations

**Add industry-specific rules:**
```python
**Guidelines for Your Industry:**
- Vendor X → Category Y
- Transactions over $500 → Special Category
- Monthly recurring → Subscription
```

**Adjust confidence logic:**
```python
**Confidence Levels:**
- high: Exact merchant match + amount in expected range
- medium: Merchant match but unusual amount
- low: Unclear merchant name
```

**Add examples:**
```python
**Examples:**
- "LOBLAWS #1234" → Groceries (high confidence)
- "SHELL GAS STATION" → Transport (high confidence)
- "UNKNOWN MERCHANT" → Other (low confidence)
```

See [prompts/README.md](app/prompts/README.md) for more customization tips.

---

## Architecture

### Files Structure

```
backend/
├── app/
│   ├── prompts/
│   │   ├── categorization.py       # Prompt templates
│   │   └── README.md               # Customization guide
│   ├── services/
│   │   ├── auto_categorization.py  # Main service
│   │   └── categorization.py       # Legacy service
│   ├── schemas/
│   │   └── merchant_cache.py       # Added batch schemas
│   └── api/v1/
│       ├── ai.py                   # Added batch endpoint
│       └── transactions.py         # Enhanced CSV upload
```

### Service Layer

**auto_categorization.py** contains:

- `categorize_transactions_batch()` - Main batch function
- `categorize_single_transaction()` - Single transaction wrapper
- `_call_ai_for_categorization()` - OpenRouter API call
- `get_valid_categories()` - Category list getter

### Database

**merchant_cache table:**
- Stores AI categorization results
- Indexed on (user_id, merchant_key)
- Tracks last_used_at for analytics

---

## Usage Examples

### 1. Categorize After CSV Upload

```bash
# Upload with auto-categorization
curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
  -F "file=@statement.csv" \
  -F "auto_categorize=true"
```

### 2. Batch Categorize Existing Transactions

```bash
# Get uncategorized transaction IDs
curl "http://localhost:8000/api/v1/transactions/view?category=Uncategorized" \
  | jq '.rows[].id'

# Categorize them
curl -X POST "http://localhost:8000/api/v1/ai/categorize_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_ids": [1, 2, 3, 4, 5],
    "auto_apply": true
  }'
```

### 3. Preview Without Applying

```bash
# Set auto_apply to false to preview
curl -X POST "http://localhost:8000/api/v1/ai/categorize_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_ids": [1, 2, 3],
    "auto_apply": false
  }'
```

### 4. Frontend Integration

```javascript
// Categorize selected transactions
async function categorizeTransactions(transactionIds) {
  const response = await fetch('/api/v1/ai/categorize_batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transaction_ids: transactionIds,
      auto_apply: true
    })
  });

  const result = await response.json();

  console.log(`Categorized ${result.successful} of ${result.total_processed}`);

  return result;
}

// Upload CSV with auto-categorization
async function uploadCSV(file, autoCategorize = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('auto_categorize', autoCategorize);

  const response = await fetch('/api/v1/transactions/upload_csv', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}
```

---

## Performance

### Caching Benefits

- **First time**: ~2-3 seconds for 10 transactions (AI call)
- **Cached**: ~100ms for 10 transactions (database lookup)
- **Mixed**: Proportional to uncached count

### Batch Size Recommendations

- **Small**: 1-10 transactions - Very fast
- **Medium**: 10-50 transactions - Recommended
- **Large**: 50-100 transactions - Works but slower
- **Very Large**: 100+ transactions - Consider splitting

### Rate Limits

Amazon Nova 2 Lite (free tier):
- **Requests**: 20 per minute
- **Tokens**: 100k per day
- **Context**: 300k tokens

For large volumes, consider:
- Splitting batches
- Adding delays between requests
- Upgrading to paid model

---

## Error Handling

### Per-Transaction Errors

If one transaction fails, others continue:

```json
{
  "results": [
    {
      "transaction_id": 1,
      "category": "Groceries",
      "applied": true,
      "error": null
    },
    {
      "transaction_id": 2,
      "category": "Uncategorized",
      "applied": false,
      "error": "Invalid merchant data"
    }
  ],
  "total_processed": 2,
  "successful": 1,
  "failed": 1
}
```

### Common Errors

**No API Key:**
```json
{
  "error": "No API key configured",
  "category": "Uncategorized",
  "applied": false
}
```

**Invalid Response:**
```json
{
  "error": "Failed to parse AI response",
  "category": "Uncategorized",
  "applied": false
}
```

**Transaction Not Found:**
```json
{
  "error": "Transaction not found",
  "category": "Uncategorized",
  "applied": false
}
```

---

## Testing

### Manual Testing

```bash
# 1. Upload sample CSV
curl -X POST "http://localhost:8000/api/v1/transactions/upload_csv" \
  -F "file=@sample_statement.csv"

# 2. Get transaction IDs
curl "http://localhost:8000/api/v1/transactions/view?category=Uncategorized" \
  | jq '.rows[].id'

# 3. Categorize
curl -X POST "http://localhost:8000/api/v1/ai/categorize_batch" \
  -H "Content-Type: application/json" \
  -d '{"transaction_ids": [1,2,3], "auto_apply": true}'

# 4. Verify
curl "http://localhost:8000/api/v1/transactions/view?category=Groceries"
```

### Integration Testing

See [test_api.py](test_api.py) for automated tests.

---

## Troubleshooting

### Categories Not Applied

**Problem**: Transactions remain uncategorized

**Solutions:**
1. Check `auto_apply` is set to `true`
2. Verify API key in `.env`
3. Check transaction IDs are valid
4. Review error messages in response

### Incorrect Categories

**Problem**: AI assigns wrong categories

**Solutions:**
1. Customize prompt templates in `app/prompts/categorization.py`
2. Add more examples for specific merchants
3. Adjust confidence thresholds
4. Clear merchant cache and re-categorize

### Slow Performance

**Problem**: Categorization takes too long

**Solutions:**
1. Reduce batch size (try 10-20 at a time)
2. Check if merchant cache is being used
3. Verify network connection to OpenRouter
4. Consider upgrading to faster model

### Cache Not Working

**Problem**: Same merchants get re-categorized

**Solutions:**
1. Check `merchant_cache` table has entries
2. Verify `merchant_key` is consistent
3. Check `last_used_at` is being updated
4. Review merchant normalization logic

---

## Future Enhancements

Planned features:

1. **Background Processing** - Queue large batches
2. **Confidence Tuning** - Adjust thresholds
3. **Custom Categories** - User-defined categories
4. **Learning Mode** - Improve from user corrections
5. **Multi-Model Support** - Try different AI models
6. **Analytics Dashboard** - Categorization stats

---

## API Reference

### Endpoint Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/ai/categorize_batch` | POST | Batch categorize transactions |
| `/api/v1/transactions/upload_csv` | POST | Upload CSV (with auto-categorize) |
| `/api/v1/transactions/categories/list` | GET | Get valid categories |

### Schema Reference

**BatchCategorizationRequest:**
```typescript
{
  transaction_ids: number[],
  auto_apply?: boolean  // default: true
}
```

**TransactionCategorizationResult:**
```typescript
{
  transaction_id: number,
  category: string,
  note: string,
  confidence: "high" | "medium" | "low",
  applied: boolean,
  error?: string
}
```

**BatchCategorizationResponse:**
```typescript
{
  results: TransactionCategorizationResult[],
  total_processed: number,
  successful: number,
  failed: number
}
```

---

## Support

- **Documentation**: See [API_ENDPOINTS.md](API_ENDPOINTS.md)
- **Interactive Docs**: http://localhost:8000/docs
- **Prompt Customization**: See [prompts/README.md](app/prompts/README.md)

---

Built with ❤️ using OpenAI SDK + OpenRouter + Amazon Nova 2 Lite 🚀
