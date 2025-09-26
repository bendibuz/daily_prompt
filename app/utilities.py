from datetime import datetime, timezone
import phonenumbers

# --- helpers -----------------------------------------------------------------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def normalize_to_e164(raw: str, default_region: str = "US") -> str:
    """Normalize any incoming phone string to E.164 or raise ValueError."""
    num = phonenumbers.parse(raw, default_region)
    if not phonenumbers.is_valid_number(num):
        raise ValueError(f"Invalid phone number: {raw}")
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
