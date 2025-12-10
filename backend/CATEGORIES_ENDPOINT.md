# Categories Endpoint

## GET /api/v1/ai/categories

Get the list of valid categories that can be assigned to transactions.

### Description

Returns a simple array of category names that:
- Can be manually assigned by users
- Are recognized by the AI categorization system
- Are validated when transactions are categorized

### Request

```bash
curl "http://localhost:8000/api/v1/ai/categories"
```

### Response

```json
[
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

### Use Cases

1. **Populate Category Dropdown**
   ```javascript
   const categories = await fetch('/api/v1/ai/categories').then(r => r.json());

   categories.forEach(cat => {
     dropdown.addOption(cat);
   });
   ```

2. **Validate User Input**
   ```javascript
   const validCategories = await fetch('/api/v1/ai/categories').then(r => r.json());

   if (!validCategories.includes(userInput)) {
     alert('Invalid category');
   }
   ```

3. **Show Available Options**
   ```javascript
   const categories = await fetch('/api/v1/ai/categories').then(r => r.json());

   console.log('Available categories:', categories.join(', '));
   ```

## Comparison with Other Endpoints

### GET /api/v1/ai/categories
- **Returns**: Simple array of category names
- **Use for**: Dropdowns, validation, showing options
- **Example**: `["Groceries", "Rent", "Transport"]`

### GET /api/v1/transactions/categories/list
- **Returns**: Categories with usage statistics
- **Use for**: Analytics, category breakdown
- **Example**:
  ```json
  [
    {
      "category": "Groceries",
      "count": 45,
      "total_amount": -1234.56
    }
  ]
  ```

## Examples

### React Component

```jsx
import { useEffect, useState } from 'react';

function CategorySelect({ value, onChange }) {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch('/api/v1/ai/categories')
      .then(r => r.json())
      .then(setCategories);
  }, []);

  return (
    <select value={value} onChange={e => onChange(e.target.value)}>
      <option value="">Select Category</option>
      {categories.map(cat => (
        <option key={cat} value={cat}>{cat}</option>
      ))}
    </select>
  );
}
```

### Form Validation

```javascript
async function validateCategory(category) {
  const validCategories = await fetch('/api/v1/ai/categories')
    .then(r => r.json());

  return validCategories.includes(category);
}

// Usage
if (!await validateCategory(userInput)) {
  showError('Please select a valid category');
}
```

### Category Filter UI

```javascript
async function buildCategoryFilters() {
  const categories = await fetch('/api/v1/ai/categories')
    .then(r => r.json());

  const filterContainer = document.getElementById('filters');

  categories.forEach(cat => {
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = cat;
    checkbox.id = `cat-${cat}`;

    const label = document.createElement('label');
    label.htmlFor = `cat-${cat}`;
    label.textContent = cat;

    filterContainer.appendChild(checkbox);
    filterContainer.appendChild(label);
  });
}
```

## Modifying Categories

To change the available categories, edit [app/services/auto_categorization.py](app/services/auto_categorization.py:19-30):

```python
VALID_CATEGORIES = [
    "Your",
    "Custom",
    "Categories",
    "Here"
]
```

The endpoint will automatically return your custom categories.

## API Documentation

This endpoint is documented in the interactive API docs:
- http://localhost:8000/docs#/ai/get_available_categories_api_v1_ai_categories_get
