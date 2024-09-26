import re
import sys
from typing import Any, Optional, Dict
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
    comment = extract_comment(commit_msg, time)

    return {
        "issue_key": jira_issue_key,
        "time": time,
        "comment": comment,
    }


def extract_comment(commit_msg: str, time_spent: Optional[str]) -> Optional[str]:
    """Extract the comment from the commit message.

    Args:
        commit_msg (str): The full commit message.
        time_spent (Optional[str]): The extracted time spent value.

    Returns:
        Optional[str]: The comment if present, or fallback to the message after time spent.
    """
    # First check if #comment is explicitly provided
    comment_match = re.search(r"#comment\s+(.+)", commit_msg)
    if comment_match:
        return comment_match.group(1).strip()

    # If no explicit #comment, use the remaining part of the message as the comment
    # Assuming time is already extracted, we find the part after time
    time_index = commit_msg.find(time_spent)
    if time_index != -1:
        # Everything after time spent until end or next command (if any)
        comment_part = commit_msg[time_index + len(time_spent) :].strip()
        return comment_part if comment_part else None

    return None


def extract_and_validate_time(commit_msg: str) -> Optional[str]:
    """Extract and validate the time spent from the commit message."""
    time_match = re.search(
        r"#time\s+(\S+(\s+\S+)*)", commit_msg
    )  # Match #time followed by time components
    time_spent = time_match.group(1) if time_match else None

    if not time_spent or not is_valid_time_format(time_spent):
        raise ValueError(
            "Error: Invalid or missing time format. Expected formats: 2d, 30m, 1h, 2h 30m ,etc."
        )

    return time_spent


def is_valid_time_format(time_str: str) -> bool:
    """Check if the time format is valid according to smart commit standards."""
    pattern = r"^\d+[hdm]"
    return bool(re.match(pattern, time_str))


def compose_smart_commit_message(
    issue_key: str, time: str, comment: Optional[str] = None
) -> str:
    """Compose smart commit message b

    Args:
        issue_key (str): The issue key for issue
        time (str): Time spent on issue
        comment (Optional[str], optional): Additional comments on the issue. Defaults to None.

    Returns:
        str: Composed smart commit message.
    """

    base_message = f"{issue_key} #time {time}"
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

        print(jira_commands)

        # Compose the smart commit message
        smart_commit_message = compose_smart_commit_message(
            jira_commands["issue_key"], jira_commands["time"], jira_commands["comment"]
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
