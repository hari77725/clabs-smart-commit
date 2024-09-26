import os
import re
import sys
from typing import Any, Optional
from subprocess import check_output
from InquirerPy import prompt

sys.stdin = open("/dev/tty", "r")


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


def get_commit_message_interactively() -> dict:
    """
    Interactively prompt the user for commit message details.

    Returns:
        dict: The commit message details as a dictionary.
    """

    sys.stdin = open("/dev/tty")

    questions = [
        {
            "type": "input",
            "name": "subject",
            "message": "Enter the JIRA issue key",
            "validate": lambda x: len(x) > 0 or "Subject cannot be empty",
        },
        {
            "type": "input",
            "name": "time_spent",
            "message": "Enter time spent (e.g., 1h, 30m):",
            "validate": lambda x: re.match(r"^\d+[hmwd]$", x)
            or "Invalid time format. Use 1h or 30m.",
        },
        {
            "type": "input",
            "name": "comment",
            "message": "Enter a comment (optional):",
            "default": "",
        },
        {
            "type": "list",
            "name": "transition",
            "message": "Select a transition (optional):",
            "choices": [
                "In Progress",
                "Testing Done",
                "Peer Review",
                "Review",
                "Staging Approved",
                "Staging Deployed",
                "Production Done",
                "Done",
            ],
            "default": "To Do",
        },
    ]

    return prompt(questions)


def main() -> None:

    if os.isatty(0):  # Check if stdin is a terminal
        pass
    else:
        os.system("exec < /dev/tty")

    ## Get current git branch
    branch = get_current_branch()

    print("Currently committing on branch: {}".format(branch))

    if branch not in ["main", "master", "staging"]:
        print(
            f"Commits to {branch} not permitted. Please commit to feature branch and open PR."
        )
        sys.exit(1)

    # Get commit message
    commit_msg_filepath = sys.argv[1]
    with open(commit_msg_filepath, "r") as f:
        commit_msg = f.read()

    print(f"Current commit message: {commit_msg}")

    x = input("Inter issue number")
    print("Issue number", x)

    # # Start interactive session
    # response = get_commit_message_interactively()

    # subject = response["subject"]
    # time_spent = response["time_spent"]
    # comment = response["comment"] or None
    # transition = response["transition"] or None

    # # Format the commit message
    # formatted_commit_msg = format_commit_message(
    #     subject, time_spent, comment, transition
    # )

    # # Append the Jira issue key to the commit message
    # final_commit_msg = f"{formatted_commit_msg}"

    # print(f"\nFormatted commit message:\n{final_commit_msg}")


if __name__ == "__main__":
    main()
