from typing import Optional

import podgenai.exceptions


def get_confirmation(next_task: Optional[str] = None) -> None:
    """Receive input confirmation from the user, optionally for the specified next task.

    If confirmation is refused, `InputError` is raised.
    """
    task_prompt = f" with {next_task}" if next_task else ""
    user_prompt = f"Continue{task_prompt}? [y/n]: "
    while True:
        response = input(user_prompt)
        response = response.strip().lower()
        match response:
            case "y" | "yes":
                break
            case "n" | "no":
                raise podgenai.exceptions.InputError("User canceled.")
