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


def get_current_branch() -> str:
    """Get the current branch

    Returns:
        str: Name of the current branch
    """
    return run_command("git symbolic-ref --short HEAD")


def extract_jira_issue_key(message: str) -> Optional[str]:
    """Extract the Jira issue key from a given string (e.g., branch name).

    Args:
        message (str): The input string (e.g., branch name or commit message).

    Returns:
        Optional[str]: The Jira issue key if found, otherwise None.
    """
    # match your Jira project key (e.g., CCPD1)
    project_key = r"CCPD1"
    issue_number = r"\d+"  # Issue number is numeric
    match = re.search(f"{project_key}-{issue_number}", message)
    return match.group(0) if match else None


def format_commit_message(
    subject: str,
    time_spent: str,
    comment: Optional[str] = None,
    transition: Optional[str] = None,
) -> str:
    """
    Format the commit message into the smart commit format.

    Args:
        subject (str): The first line of the commit message.
        time_spent (str): The time spent to log for the Jira issue.
        comment (Optional[str]): Optional comment to add to the Jira issue.
        transition (Optional[str]): Optional transition to move the issue state.

    Returns:
        str: The formatted smart commit message.
    """
    # Capitalize the first letter of the subject and remove trailing period(s)
    formatted_subject = f"{subject[:1].upper()}{subject[1:]}"
    formatted_subject = re.sub(r"\.+$", "", formatted_subject)

    # Construct the smart commit message
    jira_commands = [
        f"#{key} {value}"
        for key, value in [
            ("time", time_spent),
            ("comment", comment),
            ("transition", transition),
        ]
        if value
    ]

    # Join the command parts
    return f"{formatted_subject} " + " ".join(jira_commands)


def extract_jira_issue_key(message: str) -> Optional[str]:
    """Extract the Jira issue key from a given string (e.g., commit message).

    Args:
        message (str): The input string (e.g., branch name or commit message).

    Returns:
        Optional[str]: The Jira issue key if found, otherwise None.
    """
    project_key = r"CCDP1"  # Adjust to match your Jira project key
    issue_number = r"\d+"  # Issue number is numeric
    match = re.search(f"{project_key}-{issue_number}", message)
    return match.group(0) if match else None


def extract_jira_commands(commit_msg: str) -> Optional[dict]:
    """Extract Jira commands from the commit message.

    Args:
        commit_msg (str): The full commit message.

    Returns:
        Optional[dict]: Dictionary with issue key, time spent, comment, and transition.
    """
    jira_issue_key = extract_jira_issue_key(commit_msg)
    time_match = re.search(r"#time (\S+)", commit_msg)
    comment_match = re.search(r"#comment (.+?)(?=\n|$)", commit_msg)
    transition_match = re.search(r"#transition (\S+)", commit_msg)

    return {
        "issue_key": jira_issue_key,
        "time": time_match.group(1) if time_match else None,
        "comment": comment_match.group(1).strip() if comment_match else None,
        "transition": transition_match.group(1) if transition_match else None,
    }


def append_jira_commands(
    jira_issue_key: str,
    time_spent: str,
    comment: Optional[str] = None,
    transition: Optional[str] = None,
) -> str:
    """Generate Jira smart commit commands to append to the commit message.

    Args:
        jira_issue_key (str): The Jira issue key extracted from the branch name.
        time_spent (str): The time spent to log for the Jira issue.
        comment (Optional[str]): Optional comment to add to the Jira issue.
        transition (Optional[str]): Optional transition to move the issue state.

    Returns:
        str: Formatted Jira smart commit commands to append to the commit message.
    """
    jira_commands = [
        f"#{key} {value}"
        for key, value in [
            ("time", time_spent),
            ("comment", comment),
            ("transition", transition),
        ]
        if value
    ]

    return f"\n\n{jira_issue_key} " + " ".join(jira_commands)


def main() -> None:

    ## Get current git branch
    branch = get_current_branch()

    if branch not in ["main", "master", "staging"]:
        print(
            f"Commits to {branch} not permitted. Please commit to feature branch and open PR."
        )

    # jira_issue_key = extract_jira_issue_key(branch)
    # if not jira_issue_key:
    #     sys.exit(0)

    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        commit_msg = f.read()

    # Extract Jira commands from commit message
    jira_commands = extract_jira_commands(commit_msg)

    if not jira_commands["issue_key"]:
        print("Error: Jira issue key is mandatory in the commit message.")
        sys.exit(1)

    if not jira_commands["time"]:
        print("Error: Time spent is mandatory in the commit message.")
        sys.exit(1)

    # Here you can use the extracted values as needed
    print(f"Extracted issue key: {jira_commands['issue_key']}")
    print(f"Time spent: {jira_commands['time']}")
    print(f"Comment: {jira_commands['comment']}")
    print(f"Transition: {jira_commands['transition']}")


if __name__ == "__main__":
    main()
