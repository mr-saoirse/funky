from funkyprompt.core.agents import CallingContext
from .gpt import GptModel


def model_client_from_context(context: CallingContext):
    """The model is loaded from the context.

    This context is passed on every invocation anyway so this narrows it down to an api provider or client
    - open ai
    - llama
    - gemini
    - claude

    Within each of these providers the context can choose a model size/version
    """

    """default"""
    return GptModel()
