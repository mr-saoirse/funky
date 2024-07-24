from funkyprompt.core.agents import CallingContext
from .gpt import GptModel


def language_model_client_from_context(context: CallingContext, with_retries: int = 0):
    """The model is loaded from the context.
    Retries are used sparingly for some system contexts that require robustness
    e.g. in formatting issues for structured responses

    This context is passed on every invocation anyway so this narrows it down to an api provider or client
    - open ai
    - llama
    - gemini
    - claude

    Within each of these providers the context can choose a model size/version
    """

    """default"""
    return GptModel()
