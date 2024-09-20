class Error(Exception):
    """Base error."""


class EnvError(Error, EnvironmentError):
    """Environment variable availability error."""


class InputError(Error, ValueError):
    """Input validity error."""


class ModelOutputError(Error):
    """Model output error."""


class LanguageModelOutputError(ModelOutputError):
    """Language model output error."""


class LanguageModelOutputRejectionError(LanguageModelOutputError):
    """Language model output rejection error."""


class LanguageModelOutputStructureError(LanguageModelOutputError):
    """Language model output structure error."""
