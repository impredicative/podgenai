import podgenai.exceptions


def get_confirmation(task: str | None = None) -> None:
    """Receive input confirmation from the user, optionally for the specified task.

    If confirmation is refused, `InputError` is raised.
    """
    task_prompt = f" with {task}" if task else ""
    user_prompt = f"Continue{task_prompt}? [y/n]: "
    while True:
        response = input(user_prompt)
        response = response.strip().lower()
        match response:
            case "y" | "yes":
                break
            case "n" | "no":
                raise podgenai.exceptions.InputError("User canceled.")


def get_confirmation_or_int(range_: range, *, task: str | None = None) -> None | int:
    """Receive input confirmation from the user, optionally for the specified task.

    If the user enters an integer in the allowed range, it is returned.

    If confirmation is refused, `InputError` is raised.
    """
    task_prompt = f" with {task}" if task else ""
    user_prompt = f"Continue{task_prompt}? [y/n or integer from {min(range_)} to {max(range_)}]: "
    while True:
        response = input(user_prompt)
        response = response.strip().lower()
        match response:
            case "y" | "yes":
                break
            case "n" | "no":
                raise podgenai.exceptions.InputError("User canceled.")
            case _:
                try:
                    value = int(response)
                    if value in range_:
                        return value
                except ValueError:
                    pass
