import re
# from levenshtein import distance
from app.models.models import MessageActions
from typing import List, Dict, Any

# Accepts: " - 3", ": 3", " x3", "(3)", "[3]", "{3}", "3", "3 pt", "3 pts", "3 points" at the END
POINTS_RE = re.compile(
    r"""(?:\s*(?:[-:x]\s*|[\(\[\{]\s*))?      # optional delimiter or opening bracket
        (\d+)\s*                              # the number
        (?:pts?|points?)?                     # optional unit
        [\)\]\}]?\s*$                         # optional closing bracket then end
    """,
    re.IGNORECASE | re.VERBOSE
)

def split_on_delimiters(message: str) -> List[str]:
    delimiters = [',', ';', '|']
    regex_pattern = '|'.join(map(re.escape, delimiters))
    return [part.strip() for part in re.split(regex_pattern, message) if part.strip()]

def split_on_newlines(message: str) -> List[str]:
    return [line.strip() for line in message.splitlines() if line.strip()]

def strip_all_symbols(message: str) -> str:
    # Remove all non-alphanumeric characters except spaces
    return re.sub(r'[^a-zA-Z0-9\s]', '', message)


def extract_completed(part: str) -> str:
    """
    Extract the goal text from a 'done' line.
    Handles 'done', 'done:', 'DONE -', etc., preserves punctuation in the goal.
    """
    m = re.match(r'^\s*done\b[:\-\s]*', part, flags=re.IGNORECASE)
    if not m:
        # Fallback: if it somehow slips through, return trimmed original
        return part.strip()
    return part[m.end():].strip()

def extract_new_goal(part: str) -> Dict[str, int | str]:
    """
    Parse a goal line and optional trailing points indicator.
    Defaults to 1 point if none found.
    """
    text = part.strip()
    points = 1
    m = POINTS_RE.search(text)
    if m:
        points = int(m.group(1))
        text = text[:m.start()].rstrip()
    # Collapse inner whitespace
    text = re.sub(r'\s+', ' ', text)
    return {"goal_text": text, "points": points}

def parse_message(message: str) -> MessageActions:
    parsed_actions = MessageActions()

    stripped = re.sub(r'[^a-z0-9\s]', '', message.lower())  # cheap normalize for commands

    # Special cases
    if stripped in {"yes", "signup", "sign up"}:
        parsed_actions.signup = True
        return parsed_actions
    if stripped in {"stop", "unsubscribe", "end"}:
        parsed_actions.unsubscribe = True
        return parsed_actions
    if stripped == "help":
        parsed_actions.help = True
        return parsed_actions

    new_goals: List[Dict[str, int | str]] = []
    completed: List[str] = []

    # Split only on newlines per your examples
    for part in (line.strip() for line in message.splitlines() if line.strip()):
        if re.match(r'^\s*done\b', part, flags=re.IGNORECASE):
            done_text = extract_completed(part)
            if done_text:  # ignore empty 'done' lines
                completed.append(done_text)
        else:
            goal = extract_new_goal(part)
            if goal["goal_text"]:
                new_goals.append(goal)

    parsed_actions.new_goals = new_goals
    parsed_actions.mark_done = completed
    return parsed_actions