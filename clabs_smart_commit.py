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


def main() -> None:

    ## Get current git branch
    branch = get_current_branch()

    print('Currently committing on branch: {}'.format(branch))

    if branch not in ["main", "master", "staging"]:
        print(
            f"Commits to {branch} not permitted. Please commit to feature branch and open PR."
        )
        sys.exit(1)

    jira_issue_key = extract_jira_issue_key(branch)
    if not jira_issue_key:
        sys.exit(0)

    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        commit_msg = f.read()

    if "#time" not in commit_msg:
        print("Error: Time spent is mandatory in the commit message.")
        sys.exit(1)

    subject = commit_msg.split("#time")[
        0
    ].strip()  # Get everything before #time as the subject
    time_spent = commit_msg.split("#time")[1].strip()  # Get everything after #time
    time_spent = time_spent.split()[0]  # Extract only the time spent value

    comment = None
    transition = None
    if "#comment" in commit_msg:
        comment = commit_msg.split("#comment")[1].strip().split()[0]
    if "#transition" in commit_msg:
        transition = commit_msg.split("#transition")[1].strip().split()[0]

    # Format the commit message
    formatted_commit_msg = format_commit_message(
        subject, time_spent, comment, transition
    )

    # Append the Jira issue key to the commit message
    formatted_commit_msg = f"{jira_issue_key} {formatted_commit_msg}"

    # Override commit message
    with open(commit_msg_filepath, "w") as f:
        f.write(formatted_commit_msg)


if __name__ == "__main__":
    main()
