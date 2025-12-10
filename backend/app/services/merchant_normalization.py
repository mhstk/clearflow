import re


def normalize_merchant(description_raw: str) -> str:
    """
    Normalize raw transaction descriptions into a merchant_key.

    Process:
    - Uppercase
    - Remove digits
    - Remove extra punctuation
    - Collapse whitespace
    - Return a relatively stable key for the same merchant

    Examples:
    - "MCDONALD'S #41147 OSHAWA" -> "MCDONALDS"
    - "PRESTO APPL/Q8BPBPZ5Z2 TORONTO" -> "PRESTOAPPL"
    - "TST-Nest Uxbridge" -> "TSTNEST"
    """
    if not description_raw:
        return "UNKNOWN"

    # Uppercase
    normalized = description_raw.upper()

    # Remove digits
    normalized = re.sub(r'\d+', '', normalized)

    # Remove common separators and punctuation, keep only letters and spaces
    normalized = re.sub(r'[^A-Z\s]', ' ', normalized)

    # Collapse multiple spaces into one
    normalized = re.sub(r'\s+', ' ', normalized)

    # Strip leading/trailing spaces
    normalized = normalized.strip()

    # Take first 2-3 words (or up to 50 chars) to create a stable key
    words = normalized.split()
    if len(words) >= 2:
        # Take first 2 words for most cases
        normalized = ' '.join(words[:2])

    # Remove all spaces for final key
    normalized = normalized.replace(' ', '')

    return normalized if normalized else "UNKNOWN"
