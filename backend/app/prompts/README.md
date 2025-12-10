# AI Prompt Templates

This directory contains prompt templates for AI-powered features.

## Files

### categorization.py

Contains prompts for transaction categorization:
- `get_batch_categorization_prompt()` - For categorizing multiple transactions at once
- `get_single_categorization_prompt()` - For categorizing a single transaction

## Customization

You can modify the prompts to:
- Add more examples for specific merchants
- Adjust the tone and style
- Add domain-specific guidelines
- Change categorization logic

## Example Modifications

### Adding Industry-Specific Categories

```python
**Guidelines for Healthcare:**
- Pharmacies → Healthcare
- Doctors, Dentists → Healthcare
- Medical supplies → Healthcare
```

### Adjusting Confidence Thresholds

```python
**Confidence Levels:**
- high: Very clear merchant name match
- medium: Reasonable match but could be ambiguous
- low: Merchant name is unclear or could fit multiple categories
```

### Custom Rules

```python
**Special Rules:**
- Transactions under $5 at coffee shops → Eating Out
- Transactions over $200 at department stores → Shopping
- Regular monthly charges → Subscription
```

## Testing Prompts

After modifying prompts, test with:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/categorize_batch" \
  -H "Content-Type: application/json" \
  -d '{"transaction_ids": [1, 2, 3]}'
```

## Best Practices

1. **Be Specific**: Include clear examples for common merchants
2. **Keep It Concise**: Long prompts can reduce accuracy
3. **Use Constraints**: Always specify valid categories
4. **Request JSON**: Structured output is easier to parse
5. **Include Context**: Amount and date help with ambiguous merchants
