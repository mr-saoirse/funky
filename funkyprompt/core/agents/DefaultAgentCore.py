"""this example illustrates how "agents" are just objects with properties and functions
  some agents may not have properties 
  but properties act as a response template which will be a json response.
"""

from funkyprompt.core import AbstractModel
import typing


AGENT_CORE_DESCRIPTION = """
As an agent you are responsible for calling 
provide functions to answer the users question.
The default agent core contains basic bootstrapping functions. 

An example use case would be to ask questions about 
named entities which can be loaded from the store. 
Once loaded, these entities provide not only details 
but references to other functions that can be called. 
This can be used to allows agent workflows to multi-hop.

Furthermore, a help function can be used for general planning 
over all known functions in a function registry.
These functions are loaded on demand into the runners for use by LLMs.

Image description functions points to some multimodal applications.
"""


class DefaultAgentCore(AbstractModel):
    """Agents in `funkyprompt` are declarative things.
    They do not do anything except expose metadata and functions.
    Runners are used to manage the comms with LLMS
    and the basic workflow - there is only one workflow in `funkyprompt`.
    This default type for use in the runner - contains basic functions.
    This minimal agent is quite powerful because it can bootstrap RAG/search.
    """

    class Config:
        name: str = "agent"
        namespace: str = "core"
        description: str = AGENT_CORE_DESCRIPTION

    def help(self, context: str) -> dict:
        """
        Ask for help or functions needed to answer
        the users question or to solve the problem.
        This can be used to fetch functions via a function manager
        and these functions will be loaded into context

        Args:
            context: the question or context to ask for help
        """
        pass

    def describe_images(self, images: typing.List[str], question: str = None) -> dict:
        """describe a set of using the default LLM and an optional prompt/question

        Args:
            images (typing.List[str]): the images in uri format or Pil Image format
            question (str): the question to ask about the images - optional, a default prompt will be used
        """
        pass

    def lookup_entity(self, keys: str | typing.List[str]) -> typing.List[dict]:
        """Given one or more entity keys, lookup the entity details

        Args:
            keys (str | typing.List[str]): a list of one or more keys

        Returns: a list of typed entities
        """
