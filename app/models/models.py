from dataclasses import dataclass, field
from typing import Optional
from typing import List
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

#In the backend, user messages are decoded into goals when appropriate, and updated
@dataclass
class Goal:
    goal_text: str
    points: int = 0
    complete: bool = False
    created_at: Optional[datetime] = field(default_factory=utcnow)
    updated_at: Optional[datetime] = None

@dataclass
class Day:
    datekey: str = ""
    total_points: int = 0
    completed_points: int = 0
    created_at: Optional[datetime] = field(default_factory=utcnow)
    updated_at: Optional[datetime] = None
    goals: List[Goal] = field(default_factory=list)


@dataclass
class PhoneBinding:  # reverse index: phone -> user
    # Use E.164 as the document ID in Firestore
    e164: str
    user_id: str                 # your UID
    verified: bool = False
    bound_at: datetime = field(default_factory=utcnow)
    released_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)

@dataclass
class UserPhone:
    e164: str
    verified: bool = False
    label: Optional[str] = None
    added_at: datetime = field(default_factory=utcnow)
    last_seen: Optional[datetime] = None

@dataclass
class UserDoc:
    user_id: str                 # Firestore UID or UUID
    display_name: Optional[str]
    email: Optional[str]         # store only if you actually use it
    timezone: str = "America/Chicago"
    phones: List[UserPhone] = field(default_factory=list)
    activated: bool = False
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

# Inbound Twilio message
@dataclass
class UserMessage:
    message: str
    phone_number: str
    timestamp: datetime = field(default_factory=utcnow)
    uid: Optional[str] = None