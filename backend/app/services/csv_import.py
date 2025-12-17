import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from sqlalchemy.orm import Session
from io import BytesIO

from app.models.account import Account
from app.models.transaction import Transaction
from app.services.merchant_normalization import normalize_merchant

logger = logging.getLogger(__name__)


def parse_rbc_csv(
    file_content: bytes,
    db: Session,
    user_id: int,
    account_id: Optional[int] = None
) -> Tuple[int, int, int]:
    """
    Parse RBC-style CSV and import transactions.

    Returns: (inserted_count, skipped_count, account_id)
    """
    # Read CSV with pandas
    df = pd.read_csv(BytesIO(file_content))

    # Expected columns
    required_cols = ["Account Type", "Account Number", "Transaction Date",
                     "Description 1", "Description 2", "CAD$"]

    # Check if required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    inserted_count = 0
    skipped_count = 0

    # Get or create account
    if account_id is None:
        # Use first row to determine account details
        first_row = df.iloc[0]
        account_type = str(first_row["Account Type"]).strip()
        account_number = str(first_row["Account Number"]).strip()
        account_number_last4 = account_number[-4:] if len(account_number) >= 4 else account_number

        # Try to find existing account
        account = db.query(Account).filter(
            Account.user_id == user_id,
            Account.account_type == account_type,
            Account.account_number_last4 == account_number_last4
        ).first()

        if not account:
            # Create new account
            account = Account(
                user_id=user_id,
                name=f"{account_type} •••• {account_number_last4}",
                account_type=account_type,
                account_number_last4=account_number_last4,
                currency="CAD"
            )
            db.add(account)
            db.commit()
            db.refresh(account)

        account_id = account.id

    # Process each transaction
    for _, row in df.iterrows():
        try:
            # Parse date (format: MM/DD/YYYY)
            transaction_date_str = str(row["Transaction Date"]).strip()
            transaction_date = datetime.strptime(transaction_date_str, "%m/%d/%Y").date()

            # Determine amount and currency
            cad_amount = row.get("CAD$")
            usd_amount = row.get("USD$")

            amount = None
            currency = "CAD"

            if pd.notna(cad_amount) and cad_amount != "":
                amount = float(cad_amount)
                currency = "CAD"
            elif pd.notna(usd_amount) and usd_amount != "":
                amount = float(usd_amount)
                currency = "USD"

            # Skip if no amount
            if amount is None:
                skipped_count += 1
                continue

            # Build description
            desc1 = str(row["Description 1"]).strip() if pd.notna(row["Description 1"]) else ""
            desc2 = str(row["Description 2"]).strip() if pd.notna(row["Description 2"]) else ""
            description_raw = f"{desc1} {desc2}".strip()

            if not description_raw:
                skipped_count += 1
                continue

            # Normalize merchant
            merchant_key = normalize_merchant(description_raw)

            # Create transaction
            transaction = Transaction(
                account_id=account_id,
                user_id=user_id,
                date=transaction_date,
                description_raw=description_raw,
                merchant_key=merchant_key,
                amount=amount,
                currency=currency,
                category="Uncategorized",
                category_source="uncategorized",
                is_expense=amount < 0  # True for expenses (negative), False for income (positive)
            )

            db.add(transaction)
            inserted_count += 1

        except Exception as e:
            print(f"Error processing row: {e}")
            skipped_count += 1
            continue

    # Commit all transactions
    db.commit()

    return inserted_count, skipped_count, account_id


def parse_csv_universal(
    file_content: bytes,
    format_config: Dict,
    db: Session,
    user_id: int,
    account_id: Optional[int] = None
) -> Tuple[int, int, int]:
    """
    Parse any bank CSV using AI-detected format configuration.

    Args:
        file_content: Raw CSV file content
        format_config: Dictionary with column mappings from AI detection
        db: Database session
        user_id: Current user ID
        account_id: Optional existing account ID

    Returns: (inserted_count, skipped_count, account_id)
    """
    # Read CSV with pandas
    try:
        df = pd.read_csv(BytesIO(file_content))
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        raise ValueError(f"Could not read CSV file: {e}")

    # Extract format config
    date_column = format_config.get("date_column")
    date_format = format_config.get("date_format", "%Y-%m-%d")
    description_columns = format_config.get("description_columns", [])
    amount_column = format_config.get("amount_column")
    amount_is_absolute = format_config.get("amount_is_absolute", False)
    sign_column = format_config.get("sign_column")
    debit_indicators = [s.lower() for s in format_config.get("debit_indicators", [])]
    credit_indicators = [s.lower() for s in format_config.get("credit_indicators", [])]
    currency = format_config.get("currency", "CAD")
    account_type_column = format_config.get("account_type_column")
    account_number_column = format_config.get("account_number_column")

    # Validate required columns exist
    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in CSV")
    if amount_column not in df.columns:
        raise ValueError(f"Amount column '{amount_column}' not found in CSV")

    inserted_count = 0
    skipped_count = 0

    # Get or create account
    if account_id is None:
        account_id = _get_or_create_account(
            df, db, user_id, currency,
            account_type_column, account_number_column
        )

    # Process each row
    for idx, row in df.iterrows():
        try:
            # Parse date
            date_str = str(row[date_column]).strip()
            if not date_str or date_str.lower() == 'nan':
                skipped_count += 1
                continue

            try:
                transaction_date = datetime.strptime(date_str, date_format).date()
            except ValueError:
                # Try common alternative formats
                transaction_date = _parse_date_flexible(date_str)
                if not transaction_date:
                    logger.warning(f"Could not parse date: {date_str}")
                    skipped_count += 1
                    continue

            # Parse amount
            amount_str = str(row[amount_column]).strip()
            amount_str = amount_str.replace(',', '').replace('$', '').replace('"', '')

            if not amount_str or amount_str.lower() == 'nan':
                skipped_count += 1
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                logger.warning(f"Could not parse amount: {amount_str}")
                skipped_count += 1
                continue

            # Handle amount sign based on format config
            if amount_is_absolute and sign_column:
                sign_value = str(row.get(sign_column, "")).strip().lower()
                if sign_value in debit_indicators:
                    amount = -abs(amount)  # Debit = expense = negative
                elif sign_value in credit_indicators:
                    amount = abs(amount)  # Credit = income = positive
                # If sign_value not recognized, keep original

            # Build description from configured columns
            description_parts = []
            for col in description_columns:
                if col in df.columns:
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip():
                        description_parts.append(str(val).strip())

            description_raw = " ".join(description_parts)

            if not description_raw:
                # Fallback: use first non-empty string column
                for col in df.columns:
                    val = row.get(col)
                    if pd.notna(val) and isinstance(val, str) and val.strip():
                        description_raw = val.strip()
                        break

            if not description_raw:
                skipped_count += 1
                continue

            # Normalize merchant
            merchant_key = normalize_merchant(description_raw)

            # Create transaction
            transaction = Transaction(
                account_id=account_id,
                user_id=user_id,
                date=transaction_date,
                description_raw=description_raw,
                merchant_key=merchant_key,
                amount=amount,
                currency=currency,
                category="Uncategorized",
                category_source="uncategorized",
                is_expense=amount < 0
            )

            db.add(transaction)
            inserted_count += 1

        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}")
            skipped_count += 1
            continue

    # Commit all transactions
    db.commit()

    logger.info(f"Universal parser: inserted={inserted_count}, skipped={skipped_count}")
    return inserted_count, skipped_count, account_id


def _get_or_create_account(
    df: pd.DataFrame,
    db: Session,
    user_id: int,
    currency: str,
    account_type_column: Optional[str],
    account_number_column: Optional[str]
) -> int:
    """Get existing account or create a new one based on CSV data."""

    account_type = "Bank Account"
    account_number_last4 = "0000"

    # Try to extract account info from CSV
    if account_type_column and account_type_column in df.columns:
        first_valid = df[account_type_column].dropna().iloc[0] if not df[account_type_column].dropna().empty else None
        if first_valid:
            account_type = str(first_valid).strip()

    if account_number_column and account_number_column in df.columns:
        first_valid = df[account_number_column].dropna().iloc[0] if not df[account_number_column].dropna().empty else None
        if first_valid:
            account_number = str(first_valid).strip()
            account_number_last4 = account_number[-4:] if len(account_number) >= 4 else account_number

    # Try to find existing account
    account = db.query(Account).filter(
        Account.user_id == user_id,
        Account.account_type == account_type,
        Account.account_number_last4 == account_number_last4
    ).first()

    if not account:
        # Create new account
        account = Account(
            user_id=user_id,
            name=f"{account_type} •••• {account_number_last4}",
            account_type=account_type,
            account_number_last4=account_number_last4,
            currency=currency
        )
        db.add(account)
        db.commit()
        db.refresh(account)

    return account.id


def _parse_date_flexible(date_str: str):
    """Try multiple date formats to parse a date string."""
    formats = [
        "%Y-%m-%d",      # 2025-12-15
        "%m/%d/%Y",      # 12/15/2025
        "%d/%m/%Y",      # 15/12/2025
        "%m-%d-%Y",      # 12-15-2025
        "%d-%m-%Y",      # 15-12-2025
        "%Y/%m/%d",      # 2025/12/15
        "%d %b %Y",      # 15 Dec 2025
        "%d-%b-%Y",      # 15-Dec-2025
        "%b %d, %Y",     # Dec 15, 2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None
