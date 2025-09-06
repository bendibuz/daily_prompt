from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    display_name: str
    password: str
    phone_number: str
    email: str

@dataclass
class UserMessage:
    user_id: str
    message: str
    timestamp: str
    phone_number: Optional[str] = None

@dataclass
class Goal:
    goal_text: str
    points: int
    complete: bool