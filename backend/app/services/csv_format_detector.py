"""
AI-powered CSV format detection service.

Analyzes bank CSV exports to automatically detect column mappings,
date formats, and amount conventions for any bank.
"""

import httpx
import json
import logging
import pandas as pd
from typing import Dict, Optional
from io import StringIO, BytesIO

from app.core.config import settings

logger = logging.getLogger(__name__)

# Default format config for RBC (fallback)
RBC_FORMAT = {
    "has_header": True,
    "date_column": "Transaction Date",
    "date_format": "%m/%d/%Y",
    "description_columns": ["Description 1", "Description 2"],
    "amount_column": "CAD$",
    "amount_fallback_column": "USD$",
    "debit_column": None,
    "credit_column": None,
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

First decide whether the file has a header row:
- has_header: true if the first row contains column labels; false if the first row is already transaction data.
- If has_header is FALSE, reference every column by its 0-based integer index (0, 1, 2, ...).
- If has_header is TRUE, reference every column by its exact header name.

Return a JSON object with these fields:
- has_header: true or false
- date_column: column (name or index) containing the transaction date (required)
- date_format: Python strptime format string (e.g., "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")
- description_columns: array of columns to combine for the merchant description
- amount_column: the single column holding the signed amount, OR null if the file uses separate debit/credit columns
- debit_column: column for money OUT / charges / purchases (expenses), or null
- credit_column: column for money IN / payments / refunds (income), or null
- amount_is_absolute: true if amounts are always positive (need sign_column to determine debit/credit)
- sign_column: column indicating debit/credit (null if the amount is already signed or split into debit/credit columns)
- debit_indicators: array of sign_column values that mean expense/debit (e.g., ["Debit", "DR", "D"])
- credit_indicators: array of sign_column values that mean income/credit (e.g., ["Credit", "CR", "C"])
- currency: detected currency code (default "CAD")
- account_type_column: column for account type (null if not present)
- account_number_column: column for account/card number (null if not present)

Important rules:
- Use debit_column + credit_column (and set amount_column to null) when the file has one column for charges and a separate column for payments; each row fills only one of them.
- Otherwise use amount_column and leave debit_column/credit_column null.
- If the single amount column has negative values for expenses, set amount_is_absolute to false.
- If amount is always positive with a separate transaction-type column, set amount_is_absolute to true.
- Common date formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, DD-MMM-YYYY.
- Combine relevant description columns (merchant name, location, etc.).

Example for a headerless file with separate debit/credit columns
(date, description, charge, payment, card number):
{{"has_header": false, "date_column": 0, "date_format": "%Y-%m-%d", "description_columns": [1], "amount_column": null, "debit_column": 2, "credit_column": 3, "amount_is_absolute": false, "sign_column": null, "debit_indicators": [], "credit_indicators": [], "currency": "CAD", "account_type_column": null, "account_number_column": 4}}

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

    # If no API key, fall back to RBC format
    if not settings.ai_api_key:
        logger.warning("No AI API key, using default RBC format")
        config = dict(RBC_FORMAT)
    else:
        try:
            config = await _call_openrouter_for_format(csv_sample)
            logger.info(f"AI-detected CSV format: {config}")
        except Exception as e:
            logger.error(f"Error detecting CSV format: {e}", exc_info=True)
            config = dict(RBC_FORMAT)

    # Deterministic repair: the LLM frequently mislabels separate debit/credit
    # columns (one column is mostly empty, which confuses it). Correct it from data.
    try:
        config = _repair_format_from_data(csv_content, config)
    except Exception as e:
        logger.warning(f"CSV format repair skipped: {e}")

    return config


def _repair_format_from_data(csv_content: bytes, config: Dict) -> Dict:
    """Detect a debit/credit split from the data and fix the config if needed.

    Triggers only when there are exactly two all-positive, mutually-exclusive numeric
    columns — the signature of separate charge/payment columns. This guard keeps it
    from misfiring on signed-amount or amount+balance layouts.
    """
    def parse_num(v):
        s = str(v).strip().replace(',', '').replace('$', '').replace('"', '')
        if not s or s.lower() == 'nan':
            return None
        try:
            return float(s)
        except ValueError:
            return None

    try:
        text_content = csv_content.decode('utf-8')
    except UnicodeDecodeError:
        text_content = csv_content.decode('latin-1')

    has_header = config.get("has_header", True)
    df = pd.read_csv(BytesIO(text_content.encode('utf-8')), header=0 if has_header else None)
    if df.empty:
        return config

    # Find numeric columns (>=90% of filled cells parse as numbers) and sign info
    numeric_cols = []
    for col in df.columns:
        filled = numeric = 0
        has_neg = False
        for v in df[col]:
            sval = str(v).strip()
            if sval and sval.lower() != 'nan':
                filled += 1
            n = parse_num(v)
            if n is not None:
                numeric += 1
                if n < 0:
                    has_neg = True
        if filled and numeric / filled >= 0.9:
            numeric_cols.append({"col": col, "filled": filled, "has_neg": has_neg})

    if len(numeric_cols) != 2:
        return config
    a, b = numeric_cols
    if a["has_neg"] or b["has_neg"]:
        return config  # signed amounts -> not a debit/credit split

    # Require mutual exclusivity: each row fills exactly one of the two columns
    both = either = 0
    for _, row in df.iterrows():
        va, vb = parse_num(row[a["col"]]), parse_num(row[b["col"]])
        if va is not None or vb is not None:
            either += 1
        if va is not None and vb is not None:
            both += 1
    if either == 0 or both / either > 0.1:
        return config  # overlapping -> likely amount+balance, not debit/credit

    # It's a debit/credit split. Pick the credit column via payment keywords.
    credit_kw = ("payment", "paiement", "merci", "credit", "refund", "thank", "deposit", "remb")
    desc_cols = config.get("description_columns") or []
    desc_col = desc_cols[0] if desc_cols else None
    a_hits = b_hits = 0
    if desc_col is not None and desc_col in df.columns:
        for _, row in df.iterrows():
            if any(k in str(row[desc_col]).lower() for k in credit_kw):
                if parse_num(row[a["col"]]) is not None:
                    a_hits += 1
                if parse_num(row[b["col"]]) is not None:
                    b_hits += 1

    if a_hits > b_hits:
        credit_col, debit_col = a["col"], b["col"]
    elif b_hits > a_hits:
        credit_col, debit_col = b["col"], a["col"]
    else:
        # Fallback: payments are rarer, so the less-filled column is credit
        credit_col, debit_col = (a["col"], b["col"]) if a["filled"] < b["filled"] else (b["col"], a["col"])

    config["debit_column"] = debit_col
    config["credit_column"] = credit_col
    config["amount_column"] = None

    # If a numeric column was mislabeled as the account number, drop it and try to
    # find a real masked card / account-number column instead.
    if config.get("account_number_column") in (a["col"], b["col"]):
        config["account_number_column"] = None
    if config.get("account_number_column") is None:
        for col in df.columns:
            if col in (debit_col, credit_col):
                continue
            sample = [str(v) for v in df[col] if pd.notna(v) and str(v).strip()][:5]
            if sample and all('*' in s or (s.replace('*', '').isdigit() and len(s.replace('*', '')) >= 6) for s in sample):
                config["account_number_column"] = col
                break

    logger.info(f"Repaired debit/credit split: debit={debit_col}, credit={credit_col}, account={config.get('account_number_column')}")
    return config


async def _call_openrouter_for_format(csv_sample: str) -> Dict:
    """Call OpenRouter API to detect CSV format."""

    prompt = CSV_FORMAT_DETECTION_PROMPT.format(csv_sample=csv_sample)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.ai_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.ai_model,
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

        # Validate required fields (use `is None` so a 0 index is valid)
        if format_config.get("date_column") is None:
            raise ValueError("Missing date_column in format config")
        if (format_config.get("amount_column") is None
                and format_config.get("debit_column") is None
                and format_config.get("credit_column") is None):
            raise ValueError("Missing amount column(s) in format config")

        # Set defaults for optional fields
        format_config.setdefault("has_header", True)
        format_config.setdefault("date_format", "%Y-%m-%d")
        format_config.setdefault("description_columns", [])
        format_config.setdefault("amount_column", None)
        format_config.setdefault("debit_column", None)
        format_config.setdefault("credit_column", None)
        format_config.setdefault("amount_is_absolute", False)
        format_config.setdefault("sign_column", None)
        format_config.setdefault("debit_indicators", [])
        format_config.setdefault("credit_indicators", [])
        format_config.setdefault("currency", "CAD")
        format_config.setdefault("account_type_column", None)
        format_config.setdefault("account_number_column", None)

        return format_config
