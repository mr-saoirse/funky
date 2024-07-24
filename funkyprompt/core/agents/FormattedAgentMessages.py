"""
These messages may need to be tested for all API formats 
"""

import typing
import json
from funkyprompt.core.agents import CallingContext
from funkyprompt.core import AbstractModel


def structure_question(
    question: str, model: AbstractModel, context: CallingContext = None
) -> typing.List[dict]:
    """Prompt building in `funkyprompt` is governed by models or types. A question is injected into a scaffold based on the type
    For language models we can construct a set of one or more messages using different roles.
    One large blob in a question can work but its often sensible to split fragments by role

    Args:
        question (str): the users question
        model (AbstractModel): the model used to generate the plan
        context (CallingContext, optional): context is used to determine the model provider and other session context. Defaults to None.
    """
    return []


def format_function_response_data(
    name: str, data: typing.Any, context: CallingContext = None
) -> dict:
    """format the function response for the agent - essentially just a json dump

    Args:
        name (str): the name of the function
        data (typing.Any): the function response
        context (CallingContext, optional): context such as what model we are using to format the message with

    Returns: formatted messages for agent as a dict
    """

    return {
        "role": "function",
        "name": f"{str(name)}",
        "content": json.dumps(
            {
                # do we need to be this paranoid most of the time?? this is a good label to point later stages to the results
                "about-these-data": "here are some data that may or may not contain the answer to your question - please review it carefully",
                "data": data,
            },
            default=str,
        ),
    }


def format_function_response_type_error(
    name: str, ex: Exception, context: CallingContext = None
) -> dict:
    """type errors imply the function was incorrectly called and the agent should try again

    Args:
        name (str): the name of the function
        data (typing.Any): the function response
        context (CallingContext, optional): context such as what model we are using to format the message with

    Returns: formatted error messages for agent as a dict
    """
    return {
        "role": "system",
        "name": f"{str(name.replace('.','_'))}",
        "content": f"""You have called the function incorrectly - try again {ex}""",
    }


def format_function_response_error(
    name: str, ex: Exception, context: CallingContext = None
) -> dict:
    """general errors imply something wrong with the function call

    Args:
        name (str): the name of the function
        data (typing.Any): the function response
        context (CallingContext, optional): context such as what model we are using to format the message with

    Returns: formatted error messages for agent as a dict
    """

    return {
        "role": "system",
        "name": f"{str(name.replace('.','_'))}",
        "content": f"""This function failed - you should try different arguments or a different function. - {ex}. 
                    If not data found you must search for another function if you can to answer the users question. 
                    Otherwise check the error and consider your input parameters """,
    }
