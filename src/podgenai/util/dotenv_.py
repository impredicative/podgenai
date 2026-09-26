import dotenv


def load_dotenv() -> None:
    """Load the .env file normally and also from the current directory."""
    # Ref: https://stackoverflow.com/a/78972639/
    dotenv.load_dotenv()
    dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))
