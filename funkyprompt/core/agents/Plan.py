from funkyprompt.core import AbstractModel

PLANNING_PROMPT = f""


class Plan(AbstractModel):
    """The plan is a recursive DAG over functions"""

    class Config:
        name: str = "plan"
        namespace: str = "core"
        description = PLANNING_PROMPT
