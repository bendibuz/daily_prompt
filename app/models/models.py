from dataclasses import dataclass, field
from typing import Optional
from typing import List
from datetime import datetime

#In the backend, user messages are decoded into goals when appropriate, and updated
@dataclass
class Goal:
    goal_text: str
    points: int = 0
    complete: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Day:
    datekey: str = ""
    total_points: int = 0
    completed_points: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    goals: List[Goal] = field(default_factory=list)

#How user data is stored in the backend
@dataclass
class UserDoc:
    uid: str
    display_name: str
    email: str
    phone_number: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    timezone: str = "America/Chicago"    


# ---- Read/aggregate view (not written verbatim to Firestore) ----
@dataclass
class User(UserDoc):
    # Materialize recent days when needed. Do NOT persist this list on the user doc.
    days: List[Day] = field(default_factory=list)

# Optional: explicit phone→uid index to resolve inbound SMS quickly
@dataclass
class PhoneIndex:
    phone_number: str   # E.164, e.g., "+18475551212"
    uid: str
    created_at: Optional[datetime] = None

# Inbound Twilio message
@dataclass
class UserMessage:
    message: str
    timestamp: datetime                       # tz-aware if possible
    phone_number: str                          # REQUIRED (for lookup)
    uid: Optional[str] = None                  # filled after phone→uid resolution