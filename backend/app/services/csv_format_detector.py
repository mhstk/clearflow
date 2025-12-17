"""
AI-powered CSV format detection service.

Analyzes bank CSV exports to automatically detect column mappings,
date formats, and amount conventions for any bank.
"""

import httpx
import json
import logging
from typing import Dict, Optional
from io import StringIO

from app.core.config import settings

logger = logging.getLogger(__name__)

# Default format config for RBC (fallback)
RBC_FORMAT = {
    "date_column": "Transaction Date",
    "date_format": "%m/%d/%Y",
    "description_columns": ["Description 1", "Description 2"],
    "amount_column": "CAD$",
    "amount_fallback_column": "USD$",
    "amount_is_absolute": False,
    "sign_column": None,
    "debit_indicators": [],
    "credit_indicators": [],
    "currency": "CAD",
    "account_type_column": "Account Type",
    "account_number_column": "Account Number"
}

CSV_FORMAT_DETECTION_PROMPT = """Analyze this bank CSV file and determine the column mapping for importing transactions.

CSV Sample (first 10 lines):
{csv_sample}

Identify the columns and return a JSON object with these fields:
- date_column: column name containing transaction date (required)
- date_format: Python strptime format string (e.g., "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")
- description_columns: array of column names to combine for merchant description
- amount_column: column name containing the transaction amount
- amount_is_absolute: true if amounts are always positive (need sign_column to determine debit/credit)
- sign_column: column name indicating debit/credit (null if amount already has +/- sign)
- debit_indicators: array of values in sign_column that mean expense/debit (e.g., ["Debit", "DR", "D"])
- credit_indicators: array of values in sign_column that mean income/credit (e.g., ["Credit", "CR", "C"])
- currency: detected currency code (default "CAD")
- account_type_column: column for account type (null if not present)
- account_number_column: column for account number (null if not present)

Important rules:
- If amount column has negative values for expenses, set amount_is_absolute to false
- If amount is always positive and there's a separate column for transaction type, set amount_is_absolute to true
- Look for common date formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, DD-MMM-YYYY
- Combine relevant description columns (merchant name, location, etc.)

Return ONLY valid JSON, no explanation or markdown."""


async def detect_csv_format(csv_content: bytes) -> Dict:
    """
    Detect CSV format using AI analysis.

    Args:
        csv_content: Raw CSV file content as bytes

    Returns:
        Dictionary with column mappings and format configuration
    """
    # Extract first 10 lines for analysis
    try:
        text_content = csv_content.decode('utf-8')
    except UnicodeDecodeError:
        text_content = csv_content.decode('latin-1')

    lines = text_content.strip().split('\n')[:10]
    csv_sample = '\n'.join(lines)

    # If no API key, return RBC format as default
    if not settings.OPENROUTER_API_KEY:
        logger.warning("No OpenRouter API key, using default RBC format")
        return RBC_FORMAT

    try:
        result = await _call_openrouter_for_format(csv_sample)
        logger.info(f"Detected CSV format: {result}")
        return result
    except Exception as e:
        logger.error(f"Error detecting CSV format: {e}", exc_info=True)
        return RBC_FORMAT


async def _call_openrouter_for_format(csv_sample: str) -> Dict:
    """Call OpenRouter API to detect CSV format."""

    prompt = CSV_FORMAT_DETECTION_PROMPT.format(csv_sample=csv_sample)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1  # Low temperature for consistent JSON output
            }
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Clean up response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Parse JSON
        format_config = json.loads(content)

        # Validate required fields
        if not format_config.get("date_column"):
            raise ValueError("Missing date_column in format config")
        if not format_config.get("amount_column"):
            raise ValueError("Missing amount_column in format config")

        # Set defaults for optional fields
        format_config.setdefault("date_format", "%Y-%m-%d")
        format_config.setdefault("description_columns", [])
        format_config.setdefault("amount_is_absolute", False)
        format_config.setdefault("sign_column", None)
        format_config.setdefault("debit_indicators", [])
        format_config.setdefault("credit_indicators", [])
        format_config.setdefault("currency", "CAD")
        format_config.setdefault("account_type_column", None)
        format_config.setdefault("account_number_column", None)

        return format_config
