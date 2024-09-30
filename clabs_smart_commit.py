import re
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from typing import Any, List, Optional, Dict
from subprocess import check_output


def run_command(command: str) -> Any:
    """Runs any command and returns its output."""
    try:
        stdout: str = check_output(command.split()).decode("utf-8").strip()
    except Exception:
        stdout = ""
    return stdout


def get_branch() -> str:
    return run_command("git symbolic-ref --short HEAD")


def extract_jira_issue_key(message: str) -> Optional[str]:
    """Extract the Jira issue key from a given string."""
    project_key = r"CCDP1"
    match = re.search(
        rf"{project_key}-(\d+)", message, re.IGNORECASE
    )  # Case insensitive
    return match.group(0).upper() if match else None


def extract_jira_commands(commit_msg: str) -> Dict[str, Optional[str]]:
    """Extract Jira commands from the commit message."""
    jira_issue_key = extract_jira_issue_key(commit_msg)
    time = extract_and_validate_time(commit_msg)
    comment = extract_comment(commit_msg, time)
    transition = extract_transition(commit_msg, jira_issue_key)

    return {
        "issue_key": jira_issue_key,
        "time": time,
        "comment": comment,
        "transition": transition,
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

    # Fallback to everything after #time or issue key if #comment isn't present
    comment_part = re.split(r"#time\s+\S+\s*|#\w+", commit_msg)[-1].strip()
    return comment_part if comment_part else None


def extract_and_validate_time(commit_msg: str) -> Optional[str]:
    """Extract and validate the time spent from the commit message."""
    time_match = re.search(
        r"#time\s+(\d+\s*[hdm](?:\s+\d+\s*[hdm])*)", commit_msg
    )  # Get time components only
    time_spent = time_match.group(1) if time_match else None

    if not time_spent or not is_valid_time_format(time_spent):
        raise ValueError(
            "Error: Invalid or missing time format. Expected formats: 2d, 30m, 1h, 2h 30m ,etc."
        )

    return time_spent


def normalize_transition(transition: str) -> str:
    """Normalize transition to lowercase and replace spaces with underscores."""
    return transition.lower().replace(" ", "_")


def extract_transition(commit_msg: str, issue_key: str) -> Optional[str]:
    """Extract the transition action from the commit message.

    Args:
        commit_msg (str): The full commit message.
        issue_key (str): The extracted issue key.

    Returns:
        Optional[str]: The transition action if present.
    """
    # Define allowed transitions
    allowed_transitions = [
        "to_do",
        "testing_done",
        "staging_deployed",
        "staging_approved",
        "review",
        "production_deployed",
        "done",
        "peer_review",
        "in_progress",
    ]

    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")

    # Get issue details
    url = f"https://customerlabs.atlassian.net/rest/api/3/issue/{issue_key}"

    auth = HTTPBasicAuth(
        jira_email,
        jira_api_token,
    )

    headers = {"Accept": "application/json"}

    response = requests.request("GET", url, headers=headers, auth=auth)

    if response.status_code != 200:
        print(
            f"Error: Failed to fetch issue details. Please check auth token and try again."
        )
        sys.exit(1)

    issue_data = response.json()

    incomplete_issues: List[str] = []

    # Check if the issue is a parent task
    if not issue_data["fields"]["issuetype"]["subtask"] and len(
        issue_data["fields"]["subtasks"]
    ):
        # Check the status of all subtasks
        for subtask in issue_data["fields"]["subtasks"]:
            subtask_key = subtask["key"]
            subtask_status = subtask["fields"]["status"]["statusCategory"]["key"]

            if subtask_status != "done":
                incomplete_issues.append(subtask_key)

        if incomplete_issues:
            print(
                f"Error: Subtasks not done: {', '.join(incomplete_issues)}. Complete subtasks before moving parent task to done."
            )
            sys.exit(1)  # Block the transition if any subtasks are not done

    states = re.findall(
        r"#(\w+)", commit_msg, re.IGNORECASE
    )  # Matches '# followed by one or more word characters'
    states = list(map(str.lower, states))

    # Return the first match that is in allowed transitions
    for state in states:
        if state in allowed_transitions:
            return state

    return None


def is_valid_time_format(time_str: str) -> bool:
    """Check if the time format is valid according to smart commit standards."""
    pattern = r"^\d+[hdm]"
    return bool(re.match(pattern, time_str))


def compose_smart_commit_message(
    issue_key: str,
    time: str,
    comment: Optional[str] = None,
    transition: Optional[str] = None,
) -> str:
    """Compose smart commit message b

    Args:
        issue_key (str): The issue key for issue
        time (str): Time spent on issue
        comment (Optional[str], optional): Additional comments on the issue. Defaults to None.
        transition (Optional[str], optional): Transition action. Defaults to None.

    Returns:
        str: Composed smart commit message.
    """

    base_message = f"{issue_key} #time {time}"
    if comment:
        base_message += f" #comment {comment}"
    if transition:
        base_message += f" #{transition}"
    return base_message


def main() -> None:

    # Check if API key and email ids are present for JIRA

    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")

    if not jira_email:
        print(
            "Error: JIRA_EMAIL environment variable is not set.\n"
            "Please set your JIRA email ID in .bashrc or .zshrc:\n"
        )
        sys.exit(1)

    if not jira_api_token:
        print(
            "Error: JIRA_API_TOKEN environment variable is not set.\n"
            "Visit the following link to generate an API token:\n"
            "https://id.atlassian.com/manage-profile/security/api-tokens \n"
            "Once generated, set it as an environment variable in .bashrc or .zshrc\n"
        )
        sys.exit(1)

    # Commit message file path from arguments
    commit_msg_filepath = sys.argv[1]

    branch = get_branch()

    if branch in ["master", "main"] or branch.startswith(("staging", "production")):
        print(
            f"Error: You're trying to commit directly to a restricted branch. Pushes to {branch} is prohibited. Please commit to a feature branch and open a PR"
        )
        sys.exit(1)

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

        if not jira_commands["comment"]:
            print("Error: Comment is mandatory in the commit message.")
            sys.exit(1)

        if not jira_commands["transition"]:
            print("Error: Transition action is mandatory in the commit message.")
            sys.exit(1)

        print(jira_commands)

        # Compose the smart commit message
        smart_commit_message = compose_smart_commit_message(
            jira_commands["issue_key"],
            jira_commands["time"],
            jira_commands["comment"],
            jira_commands["transition"],
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
