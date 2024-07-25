def ask(question, context=None, **kwargs):
    """simple model entry point"""

    from funkyprompt.services import language_model_client_from_context

    model = language_model_client_from_context()
    return model(question, context=context, **kwargs)
