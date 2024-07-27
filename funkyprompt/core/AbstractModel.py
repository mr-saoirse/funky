from pydantic import BaseModel, create_model, Field
import uuid
import typing
from funkyprompt.core.types import inspection
from funkyprompt.core.types.sql import SqlHelper

"""
names are always unique in funkyprompt for key-value entity lookups
however there are times when the name is not unique and if so the id should be generated by the system
"""
KEY_FIELD_ATTRIBUTE = "is_key"
DEFAULT_KEY_ATTRIBUTE_NAME = "name"
DEFAULT_NAMESPACE = "default"


class AbstractModel(BaseModel):
    class Config:
        name: str = "abstract_model"
        namespace: str = "core"
        description: str = "Provide a rich model description"

    id: typing.Optional[str | uuid.UUID] = Field(
        default=None,
        description="A unique hash/uuid for the entity. The name can be hashed if its marked as the key",
    )

    @classmethod
    def get_model_name(cls):
        c = getattr(cls, "Config", None)
        if c and getattr(c, "name", None):
            return c.name
        """else infer from lib"""
        s = cls.model_json_schema(by_alias=False)
        return s.get("title", cls.__name__)

    @classmethod
    def get_model_namespace(cls):
        c = getattr(cls, "Config", None)
        if c and getattr(c, "namespace", None):
            return c.namespace
        """else infer from lib"""
        # convention
        namespace = cls.__module__.split(".")[-1]
        return (
            namespace
            if namespace not in ["model", "__main__", "entity"]
            else DEFAULT_NAMESPACE
        )

    @classmethod
    def get_model_description(cls):
        """the description of the entity - import for prompting"""
        c = getattr(cls, "Config", None)
        if c and getattr(c, "description", None):
            return c.description

    @classmethod
    def get_model_fullname(cls):
        """
        the model name is our convention e.g. meta.bodies
        usually we determine this from either a config object or the type itself
        """
        return f"{cls.get_model_namespace()}.{cls.get_model_name()}"

    @classmethod
    def get_type_fullname(cls):
        """
        the object name
        """
        return f"{cls.__module__}.{cls.__name__}"

    @classmethod
    def get_model_key_field(cls):
        """
        the field that is used as the primary key if it exists
        - otherwise a unique id should be generated by the system
        all models have ids and some of additional friendly names
        """
        s = cls.model_json_schema(by_alias=False)
        key_props = [
            k for k, v in s["properties"].items() if v.get(KEY_FIELD_ATTRIBUTE)
        ]
        if len(key_props):
            return key_props[0]

    def get_key_value(cls):
        """
        return the instance key value based on the configured key attribute name
        """
        return getattr(cls, cls.get_model_key_field())

    @classmethod
    def create_model(cls, name: str, namespace: str = None, **fields):
        """
        For dynamic creation of models for the type systems
        create something that inherits from the class and add any extra fields
        """
        namespace = namespace or cls.get_model_namespace()
        return create_model(name, **fields, __module__=namespace, __base__=cls)

    # def get_dynamic_functions

    def get_dummy_values(cls):
        """dummy values useful in some automation"""
        pass

    def to_arrow(cls):
        """convert the object to its pyarrow representation"""
        pass

    @classmethod
    def sql(cls) -> SqlHelper:
        """reference the sql helper"""

        return SqlHelper(cls)

    def db_dump(self):
        """serialize complex types as we need for DBs/Postgres
        - we do things like allow for config to turn fields off
        - we map complex types to json
        - embedding are added async on a new table in our model

        """
        from funkyprompt.core.types.sql import SqlHelper
        import json

        data = vars(self)
        """control selectable fields by exclude or other attributes"""
        fields = SqlHelper.select_fields(self)

        def check_complex(v):
            if isinstance(v, dict) or isinstance(v, list):
                return json.dumps(v)
            return v

        data = {k: check_complex(v) for k, v in data.items() if k in fields}

        return data

    @classmethod
    def get_embedding_fields(cls) -> typing.Dict[str, str]:
        """returns the fields that have embeddings based on the attribute - uses our convention"""
        needs_embeddings = {}
        for k, v in cls.model_fields.items():
            extras = getattr(v, "json_schema_extra", {}) or {}
            if extras.get("embedding_provider"):
                needs_embeddings[k] = f"{k}_embedding"
        return needs_embeddings

    @classmethod
    def get_model_as_prompt(cls) -> str:
        """the model as prompt provides a schema and also the description of the model
        if the base class implements `_get_prompting_data` then data will be loaded into context
        For example this is used in function planning

        this is experimental and may not be a perfect abstraction
        """
        injected_data = ""
        if getattr(cls, "_get_prompting_data", None) is not None:
            injected_data = cls._get_prompting_data()

        from funkyprompt.core.types.pydantic import get_pydantic_properties_string

        return f"""## {cls.get_model_fullname()}
    
    *Description*: {cls.get_model_description()}
    
    *Field info*:
    {get_pydantic_properties_string(cls)}
    
    {injected_data}
    """

    #############
    ##   INSPECTION
    #############

    @classmethod
    def get_class_and_instance_methods(cls):
        """returns the methods on the type that we care about"""
        return inspection.get_class_and_instance_methods(cls)

    """
    ----------
    """

    @classmethod
    def _register(cls):
        """a not to be abused but convenient self-register in the core entity store"""
        from funkyprompt.services import entity_store

        return entity_store(cls)._create_model()


class AbstractEntity(AbstractModel):
    """the abstract entity is a sub class of model that admits a unique name"""

    name: str = Field(description="The name is unique for the entity", is_key=True)

    @classmethod
    def run_search(
        cls, questions: str | typing.List[str], limit: int = None, **kwargs
    ) -> typing.List[AbstractModel]:
        """search the entity using the default store

        Args:
            questions (str | typing.List[str]): ask one or more questions - the more the better
            limit (int, optional): provide an optional search limit. Defaults to None.
        """

        from funkyprompt.services import entity_store

        return entity_store(cls).run_search(questions, limit, **kwargs)
