from funkyprompt.core import AbstractEntity, typing, Field, OpenAIEmbeddingField
import datetime
from . import GenericEntityTypes
from pydantic import model_validator
from ast import literal_eval


class Project(AbstractEntity):
    class Config:
        name: str = "project"
        namespace: str = "public"

    name: str = Field(description="The unique name of the project")
    description: str = OpenAIEmbeddingField(
        description="The detailed description of the project"
    )
    target_completion: typing.Optional[datetime.datetime] = Field(
        default=None, description="An optional target completion date for the project"
    )
    labels: typing.Optional[typing.List[str] | str] = Field(
        default_factory=list,
        description="Optional category labels - should link to topic entities",
        entity_name=GenericEntityTypes.TOPIC,
    )

    @model_validator(mode="before")
    @classmethod
    def _types(cls, values):
        """we should be stricter in array/list types but here
        example of allowing lists as TEXT in stores
        """

        if isinstance(values.get("labels"), str):
            try:
                values["labels"] = literal_eval(values["labels"])
            except:
                pass

        return values
