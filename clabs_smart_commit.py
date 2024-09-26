import re
import sys
from typing import Any, Optional, Dict, Tuple
from subprocess import check_output


def run_command(command: str) -> Any:
    """Runs any command and returns its output."""
    try:
        stdout: str = check_output(command.split()).decode("utf-8").strip()
    except Exception:
        stdout = ""
    return stdout


def extract_jira_issue_key(message: str) -> Optional[str]:
    """Extract the Jira issue key from a given string."""
    project_key = r"CCDP1"
    match = re.search(rf"{project_key}-(\d+)", message)
    return match.group(0) if match else None


def extract_jira_commands(commit_msg: str) -> Dict[str, Optional[str]]:
    """Extract Jira commands from the commit message."""
    jira_issue_key = extract_jira_issue_key(commit_msg)
    time = extract_and_validate_time(commit_msg)
    comment = extract_comment(commit_msg)
    transition = extract_transition(commit_msg)

    return {
        "issue_key": jira_issue_key,
        "time": time,
        "comment": comment,
        "transition": transition,
    }


def extract_comment(commit_msg: str) -> Optional[str]:
    """Extract the comment from the commit message."""
    # First, check if #comment is explicitly present
    comment_match = re.search(r"#comment\s+(.+)", commit_msg)
    if comment_match:
        return comment_match.group(1).strip()
    
    # If #comment is not found, extract everything after #time and any transition
    comment_part = re.split(r"#time\s+\S+\s*|#\w+", commit_msg)[-1].strip()
    return comment_part if comment_part else None


def extract_transition(commit_msg: str) -> Optional[str]:
    """Extract and normalize the transition from the commit message."""
    # Define allowed transitions
    allowed_transitions = [
        "start", "stop", "pause", "review", "done", "peer_reviewed", "in_progress"
    ]

    # Search for a transition that matches the allowed transitions
    transition_match = re.search(r"#(\w+)", commit_msg)
    
    if transition_match:
        extracted_transition = normalize_transition(transition_match.group(1))
        if extracted_transition in allowed_transitions:
            return extracted_transition
    
    return None


def normalize_transition(transition: str) -> str:
    """Normalize the transition name to a consistent format."""
    return transition.lower().replace(" ", "_")  # Normalize spaces to underscores


def extract_and_validate_time(commit_msg: str) -> Optional[str]:
    """Extracts and validates the time spent from a commit message."""
    time_match = re.search(r"#time\s+(\S+)", commit_msg)
    time_spent = time_match.group(1) if time_match else None

    if not time_spent or not is_valid_time_format(time_spent):
        raise ValueError(
            "Error: Invalid or missing time format. Expected formats: 2d, 30m, 1h, etc."
        )

    return time_spent


def is_valid_time_format(time_str: str) -> bool:
    """Check if the time format is valid according to smart commit standards."""
    pattern = r"^\d+\s*[hdm](\s+\d+\s*[hdm])*$"
    return bool(re.match(pattern, time_str))


def compose_smart_commit_message(
    issue_key: str, time: str, comment: Optional[str] = None, transition: Optional[str] = None
) -> str:
    """Compose smart commit message."""
    base_message = f"{issue_key} #time {time}"
    if transition:
        base_message += f" #{transition}"
    if comment:
        base_message += f" #comment {comment}"
    return base_message


def main() -> None:
    # Commit message file path from arguments
    commit_msg_filepath = sys.argv[1]

    try:
        with open(commit_msg_filepath, "r") as f:
            commit_msg = f.read()

        # Extract Jira commands from commit message
        jira_commands = extract_jira_commands(commit_msg)

        if not jira_commands["issue_key"]:
            print("Error: Jira issue key is mandatory in the commit message.")
            sys.exit(1)

        if not jira_commands["time"]:
            print("Error: Time spent on issue is mandatory in the commit message.")
            sys.exit(1)

        # Compose the smart commit message
        smart_commit_message = compose_smart_commit_message(
            jira_commands["issue_key"], jira_commands["time"], jira_commands["comment"], jira_commands["transition"]
        )

        # Output the composed message for confirmation
        print(f"Composed smart commit message: {smart_commit_message}")

        # Override commit message with the formatted smart commit message
        with open(commit_msg_filepath, "w") as f:
            f.write(smart_commit_message)

    except ValueError as e:
        print(e)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Commit message file not found: {commit_msg_filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
