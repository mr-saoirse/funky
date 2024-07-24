"""
The runner can call the LLM in a loop and manage the stack of messages and functions
Function calling and streaming is handled
Open telemetry is used to publish metrics which a collector could manage
If this goes above 200 lines of codes we have failed!
"""

from funkyprompt.core import AbstractModel
from funkyprompt.core.functions import FunctionCall, FunctionManager
from funkyprompt.services.models import model_client_from_context
from funkyprompt.core import utils
from funkyprompt.core.agents import (
    CallingContext,
    DefaultAgentCore,
    LanguageModel,
)
from . import FormattedAgentMessages


class Runner:
    """Runners are simple objects that provide the interface between types and language models
    The message setup is the only function that plays with natural language.
    While almost all of the "prompting" is pushed out to types and functions,
    This setup function is the one function you can play with to make sure the comms are right with the LLM.
    For example it is here we inject plans and questions and other hints for how to run things.
    But by design, the critical guidance should be abstracted by Types and Functions.
    Beyond this, the rest is routine;
    - import type metadata and functions from the model which controls most everything
    - run an executor loop sending context to the LLM
    - implement the invocation and message setup methods to manage the function and message stack

    Under the hood the function manager handles actual function loading and searching
    """

    def __init__(self, model: AbstractModel = None):
        """
        A model is passed in or the default is used
        The reason why this is passed in is to supply a minimal set of functions
        If the model has no functions simple Q&A can still be exchanged with LLMs.
        More general the model can provide a structured response format.
        This is powerful because the model is a Pydantic annotated type but can be realized as a json response
        """
        self.model = model or DefaultAgentCore()
        self._function_manager = FunctionManager()
        self.initialize()

    def initialize(self):
        """register the functions and other metadata from the model"""
        self._context = None
        """tbd how to get messages from the model
           - these are fixed messages not changing in the loop"""
        self._base_messages = []
        """register the model's functions which can include function search"""
        self._function_manager.register(self.model)

    def setup_messages(self, question: str):
        """
        On every question asked of the instance, the messages are set up.
        This function could be overridden as this largely determines behaviour
        Note the context comes from models and data,
        which should generally be more important in guidance
        """

        def _as_sys(m):
            return {"role": "system", "content": m}

        def _as_user(m):
            return {"role": "user", "content": m}

        self._last_question = question
        self.messages = list(self._base_messages)

        """update messages from context, model and question"""
        self.messages.append(
            _as_sys(self._context.plan or self.model.get_model_prompt())
        )
        """this is added because sometimes it screws up date based queries"""
        self.messages.append(
            _as_sys(
                f"I observe the current date is {utils.dates.now()} so I should take that into account if asked questions about time",
            )
        )
        """this is added because sometimes it seems to need this nudge (TODO:)"""
        self.messages.append(
            _as_user(
                f"You can use the following functions by default {self.functions.keys()} any in some cases you may be able to search and load others",
            )
        )
        """finally add the users question"""
        self.messages.append(_as_user(question))

        """when the loop runs, function responses will be appended to messages..."""

    def invoke(self, function_call: FunctionCall):
        """Invoke function(s) and parse results into messages

        Args:
            function_call (FunctionCall): the payload send from an LLM to call a function
        """
        f = self._function_manager[function_call.name]

        try:
            """try call the function - assumes its some sort of json thing that comes back"""
            data = f(**function_call.args)
            data = FormattedAgentMessages.format_function_response_data(
                function_call.name, data, self._context
            )
            """if there is an error, how you format the message matters - some generic ones are added
            its important to make sure the format coincides with the language model being used in context
            """
        except TypeError as tex:
            data = FormattedAgentMessages.format_function_response_type_error(
                function_call.name, tex, self._context
            )
        except Exception as ex:
            data = FormattedAgentMessages.format_function_response_error(
                function_call.name, ex, self._context
            )

        """update messages with data if we can or add error messages to notify the language model"""
        self.messages.append(data)

    @property
    def functions(self):
        """provide access to the function manager's functions"""
        return self._function_manager.functions

    def run(self, question: str, context: CallingContext):
        """
        Ask a question to kick of the agent loop
        """

        """setup all the bits before running the loop"""
        self.model: LanguageModel = model_client_from_context(context)
        self._context = context
        self.setup_messages(question)

        """run the agent loop to completion"""
        for _ in range(context.max_iterations):
            response = None
            """call the model with messages and function + our system context"""
            response = self.model(
                messages=self.messages,
                context=context,
                functions=self.functions,
            )
            if isinstance(response, FunctionCall):
                """call one or more funcs and update messages"""
                self.invoke(response)
                continue
            if response is not None:
                # marks the fact that we have unfinished business
                break

        """fire telemetry"""

        """log questions to store unless disabled"""

        return response

    def dump(self):
        """dumps the messages and context to stores
        if the session is a typed objective this is updated in a slowly changing dimension
        generally audit all transactions unless disabled
        """
        pass

    def __call__(self, question: str, context: CallingContext):
        """
        Ask a question to kick of the agent loop
        """
        return self.run(question, context)
