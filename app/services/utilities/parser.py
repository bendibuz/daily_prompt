import re
# from levenshtein import distance
from app.models.models import MessageActions
from typing import List

'''
Notes on formatting:
We want to allow multiple actions in one message
We can build a MessageActions dictionary with the actions as keys and the relevant strings as values
Then further process the strings accordingly

Goal format: "<goal description> [optional<: int(points)>]
    
Done format: "done <goal description>"
Done will need to compare goal against existing goal descriptions by levenshtein distance

First check if the message starts with "done" -- if not, parse as a new goal.
TODO: Allow multiple goals/done in one message, separated by ; or , or |
'''

def split_on_delimiters(message: str) -> List[str]:
    delimiters = [',', ';', '|']
    regex_pattern = '|'.join(map(re.escape, delimiters))
    return [part.strip() for part in re.split(regex_pattern, message) if part.strip()]

def strip_all_symbols(message: str) -> str:
    # Remove all non-alphanumeric characters except spaces
    return re.sub(r'[^a-zA-Z0-9\s]', '', message)

# def find_distance(str1, str2):
#     distance = levenshtein.distance(str1, str2)
#     print(f"Distance between '{str1}' and '{str2}' is {distance}")
#     return distance

def extract_completed(message: str) -> List[str]:
    '''
    Message in format:
    done: <goal1>, <goal2>, <goal3>
    or
    done: <goal1>
    done: <goal2> ...
    '''
    goals = []
    # Split the message on common delimiters
    parts = split_on_delimiters(message)
    print(parts)
    # Remove the leading "done" from the first part if present
    if parts and parts[0].lower().startswith("done"):
        parts[0] = parts[0][4:].strip()  # Remove "done" and any leading spaces
    

    return goals

def extract_new_goals(message: str) -> List[dict]:
    '''
    Message in format:
    <goal1>: <points>, <goal2>: <points>, <goal3>: <points>
    or
    <goal1>: <points>
    <goal2>: <points> ...
    '''
    goals = []
    # Split the message on common delimiters
    parts = split_on_delimiters(message)

    for part in parts:
        # Allow :, ;, | or - as separators for points
        # If there is not points at the end, default to 1
        match = re.match(r'^(.*?)(?:\s*[:;|\-]\s*(\d+))?$', part)        
        if match:
            goal_description = match.group(1).strip()
            points = int(match.group(2)) if match.group(2) else 1
            goals.append({"description": goal_description, "points": points})
        else:
            goals.append({"description": part, "points": 1})

    return goals

def parse_message(message: str) -> str:
    parsed_actions = MessageActions()
    stripped = strip_all_symbols(message.lower())

    # Special cases for exact matches
    if stripped in ["yes","signup","sign up"]: # Special case for "yes"
        parsed_actions.yes = True
        return parsed_actions
    if stripped in ["stop","unsubscribe","end"]: # Special case for "stop"
        parsed_actions.unsubscribe = True
        return parsed_actions
    if stripped == ["help"]: # Special case for "help"
        parsed_actions.help = True
        return parsed_actions
    
    if stripped.startswith("done"):
        goals_to_mark = extract_completed(message)
        parsed_actions.mark_done(goals_to_mark)
    else:
        new_goals = extract_new_goals(message)
        parsed_actions.new_goal = new_goals
        
    return parsed_actions