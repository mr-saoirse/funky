from funkyprompt.core import AbstractModel


class FunctionManager:
    def __init__(self):
        """some options such as models or data stores to use for function loading"""
        pass

    def register(self, model: AbstractModel, include_function_search: bool = False):
        """register the functions of the model

        Args:
            model (AbstractModel): _description_
            include_function_search (bool, optional): this allows for dynamic function loading via a help command
        """
        pass

    @property
    def functions(self):
        pass
