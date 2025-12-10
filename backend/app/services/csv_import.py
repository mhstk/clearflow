import pandas as pd
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from io import BytesIO

from app.models.account import Account
from app.models.transaction import Transaction
from app.services.merchant_normalization import normalize_merchant


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
