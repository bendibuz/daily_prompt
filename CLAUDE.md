# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI-based SMS goal-tracking application that integrates with Twilio for messaging and Firebase for data storage. Users can text goals to the system, mark them complete, and receive automated prompts throughout the day. The application also supports optional serial communication with Arduino hardware for LED notifications and button input.

## Development Commands

### Setup

```bash
# Windows
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux/Mac
./venv/Scripts/Activate
pip install -r requirements.txt
```

### Running the Server

```bash
# Development (Windows)
uvicorn app.main:app --reload --proxy-headers --forwarded-allow-ips="*" --workers 1

# Production
uvicorn app.main:app

# With ngrok for Twilio webhooks
ngrok http 8000
```

### Environment Variables

Required in `.env` or as environment variables:

- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER`, `TWILIO_VERIFY_SID`, `TWILIO_FROM_NUMBER`
- `MY_PHONE_NUMBER` - Default recipient for messages
- `FIREBASE_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS` - Firebase service account (file path, raw JSON, or base64-encoded JSON)
- `USE_SERIAL` - "auto" (default), "true", or "false" - Controls serial port behavior

## Architecture

### Request Flow

1. **Twilio Webhook** → `routes.py:receive_sms()` validates signature and extracts message
2. **Message Handling** → `messaging_service.py:handle_incoming_message()` coordinates processing:
   - Normalizes phone to E.164 format
   - Resolves user via `resolve_user_id_by_phone()` (checks `phone_bindings` collection)
   - Saves raw message to Firebase `messages` collection
   - Parses message with `parser.py:parse_message()`
   - Routes to appropriate action handlers
3. **Action Execution** → Functions like `set_goals()`, `mark_done()`, `list_goals()` operate on Firebase
4. **Response** → TwiML response returned to Twilio

### Core Services

**messaging_service.py** - Main orchestration layer

- Routes incoming messages to action handlers (signup, set_goals, mark_done, list_goals, help)
- Builds TwiML responses using `MessagingResponse`
- Key functions: `handle_incoming_message()`, `commit_actions()`, `resolve_user_id_by_phone()`

**firebase_service.py** - Firestore operations

- User and goal CRUD operations
- Collections: `users/{user_id}/days/{date_key}/goals/{goal_id}`
- Functions: `create_goals_entry()`, `get_today_goals_for_user()`, `get_today_goal_refs()`
- Uses timezone-aware date keys from user's timezone setting

**auth_phone.py** - Phone number authentication

- Links phone numbers to Firebase Auth users
- Uses Twilio Verify API for SMS verification codes
- Transactional binding in `bind_phone_to_user()` prevents race conditions
- Creates `phone_bindings/{e164}` documents for fast reverse lookup

**parser.py** - Natural language message parsing

- Extracts actions from user messages: signup, stop, help, list, new goals, mark done
- Supports multi-line messages, point values with various formats
- Returns `MessageActions` dataclass with parsed commands

**Serial Integration** (optional)

- `serial_service.py` - Async serial communication with Arduino via pyserial-asyncio
- `serial_noop.py` - No-op implementation when hardware unavailable
- Started in `main.py` lifespan hook with auto/manual mode selection
- Supports LED control and button input callbacks

**Cron Service** (To be developed)

- Should send a prompt to users in the morning and in the evening.
- Morning prompt asks the users what their goals are for the day
- Evening prompt sends a list of current goals status and asks user which ones are complete
- User can respond with text like "Morning: 10AM", "Evening: 6PM" to change the prompt time
- User can respond with "stop prompt" to stop the scheduled prompting

### Data Models (models.py)

- `UserDoc` - User profile with phones array, timezone, activation status
- `Goal` - Individual goal with text, points, completion status
- `Day` - Aggregates goals for a date (unused in current code but defined)
- `PhoneBinding` - Maps E.164 phone → user_id (stored in `phone_bindings` collection)
- `MessageActions` - Parsed actions from user message

### Firestore Schema

```
users/{user_id}
  - user_id, display_name, email, phones[], timezone, activated, created_at, updated_at
  /days/{date_key}  # YYYY-MM-DD in user's timezone
    /goals/{goal_id}
      - goal_text, points, complete, created_at, completed_at

phone_bindings/{e164}
  - user_id, verified, bound_at, released_at, last_seen, labels[]

messages/{message_sid}
  - body, from, to, user_id, received_at, sid, source

user_responses/{response_id}
  - user_id, from_number, parsed (MessageActions), parse_status, source_message_sid, created_at
```

## Key Implementation Patterns

### User Lookup Strategy

Phone bindings use a two-tier approach:

1. Fast path: Check `phone_bindings/{e164}` document for `user_id`
2. Fallback: Query `users` collection where `phones` array contains E.164 number

This is implemented in `messaging_service.py:resolve_user_id_by_phone()`.

### Goal Marking Logic

`messaging_service.py:mark_done()` uses case-insensitive matching and FIFO deduplication:

- Normalizes goal text to lowercase without punctuation
- Builds index of incomplete goals
- Pops one match per requested target (handles duplicates)
- Commits all updates in a single Firestore batch

### Message Parser

`parser.py:parse_message()` extracts:

- Single-word commands (signup, stop, help, list)
- Multi-line goals with optional point values: "Goal text - 5", "Goal (3 pts)", "Goal x10"
- Done markers: "done: goal text", "DONE - goal text"

### Serial Port Auto-Detection

`main.py` uses `USE_SERIAL` environment variable:

- "auto" - Tries serial, falls back to Noop on failure
- "true" - Requires serial, crashes if unavailable
- "false" - Always uses Noop

## Testing Endpoints

`/testpath` - Mock SMS endpoint bypassing Twilio signature validation (hardcoded test phone number)

## Pending Features (from TODO comments)

- Schedule morning & afternoon goal prompts (see `cron_service.py` - not currently integrated)
- User opt-out for automated prompts
- `cron_service.py:build_afternoon_message()` has undefined `goals` variable (line 38)
