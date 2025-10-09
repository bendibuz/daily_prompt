import re
from levenshtein import distance
from app.models import MessageActions

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


def strip_to_the_bones(message: str) -> str:
    # Remove all non-alphanumeric characters except spaces
    return re.sub(r'[^a-zA-Z0-9\s]', '', message)

def find_distance(str1, str2):
    distance = levenshtein.distance(str1, str2)
    print(f"Distance between '{str1}' and '{str2}' is {distance}")
    return distance

def parse_message(message: str) -> str:
    commands = ["help", "unsubscribe", "signup", "goal", "done"]
    parsed_actions = MessageActions()
    stripped = strip_to_the_bones(message.lower())

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
        parsed_actions.mark_done = True
        # Extract the goal description after "done"
        goal_description = stripped[4:].strip()  # Remove "done" and any leading spaces
        parsed_actions.goal_description = goal_description
        return parsed_actions
    else:
        parsed_actions.set_goal = True
        # Allow :, ;, | or - as separators for points
        # If there is not points at the end, default to 1
        match = re.match(r'^(.*?)(?:\s*[:;|\-]\s*(\d+))?$', stripped)        
        if match:
            goal_description = match.group(1).strip()
            points = int(match.group(2)) if match.group(2) else 1
            parsed_actions.goal_description = goal_description
            parsed_actions.points = points
        else:
            parsed_actions.goal_description = stripped
            parsed_actions.points = 1

    print(f"Parsed actions: {parsed_actions}")
    return parsed_actions