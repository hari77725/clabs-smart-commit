import re
import sys
from typing import Any, Optional
from subprocess import check_output


def run_command(command: str) -> Any:
    """Runs any command

    Args:
        command (str): Command to run

    Returns:
        Any: Response of the command
    """
    try:
        stdout: str = check_output(command.split()).decode("utf-8").strip()
    except Exception:
        stdout = ""
    return stdout


def extract_jira_issue_key(message: str) -> Optional[str]:
    """Extract the Jira issue key from a given string (e.g., commit message).

    Args:
        message (str): The input string (e.g., branch name or commit message).

    Returns:
        Optional[str]: The Jira issue key if found, otherwise None.
    """
    project_key = r"CCDP1"
    issue_number = r"\d+"  # Issue number is numeric
    match = re.search(
        rf"{project_key}-(\d+)", message
    )  # Use a raw f-string for the regex
    return match.group(0) if match else None


def extract_jira_commands(commit_msg: str) -> Optional[dict]:
    """Extract Jira commands from the commit message.

    Args:
        commit_msg (str): The full commit message.

    Returns:
        Optional[dict]: Dictionary with issue key, time spent, and comment.
    """
    jira_issue_key = extract_jira_issue_key(commit_msg)

    # Extract the time and comment using the new function
    time, comment = extract_and_validate_time(commit_msg)

    return {
        "issue_key": jira_issue_key,
        "time": time,
        "comment": comment,
    }


def extract_and_validate_time(commit_msg: str) -> tuple:
    """Extract the time spent from the commit message and validate its format.

    Args:
        commit_msg (str): The full commit message.

    Returns:
        tuple: A tuple containing the time spent (str) and comment (str).
    """
    time_match = re.search(
        r"#time\s+(\S+)", commit_msg
    )  # Matches #time followed by a space and the time value
    comment_match = re.search(
        r"#time\s+\S+\s+(.*)", commit_msg
    )  # Matches everything after #time until the end of the message

    time_spent = time_match.group(1) if time_match else None
    comment = comment_match.group(1).strip() if comment_match else None

    if time_spent and not is_valid_time_format(time_spent):
        raise ValueError(
            f"Invalid time format '{time_spent}'. Expected formats: 2d, 30m, 1d, etc."
        )

    return time_spent, comment


def is_valid_time_format(time_str: str) -> bool:
    """Verify if the time format is valid according to smart commit standards.

    Args:
        time_str (str): The time string to verify.

    Returns:
        bool: True if the time format is valid, otherwise False.
    """
    # Matches formats like "2d", "3h", "1m", "1d 2h", etc.
    pattern = r"^\d+\s*[hdm](\s+\d+\s*[hdm])*$"
    return bool(re.match(pattern, time_str))


def main() -> None:
    # Commit message file path from arguments
    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        commit_msg = f.read()

    # Extract Jira commands from commit message
    try:
        jira_commands = extract_jira_commands(commit_msg)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(jira_commands)

    if not jira_commands["issue_key"]:
        print("Error: Jira issue key is mandatory in the commit message.")
        sys.exit(1)

    # Here you can use the extracted values as needed
    print(f"Extracted issue key: {jira_commands['issue_key']}")
    print(f"Time spent: {jira_commands['time']}")
    print(f"Comment: {jira_commands['comment']}")


if __name__ == "__main__":
    main()
