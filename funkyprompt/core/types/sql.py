from uuid import UUID
from funkyprompt.core.types import EMBEDDING_LENGTH_OPEN_AI
import typing


class SqlHelper:

    def __init__(self, model):
        self.model = model

    @staticmethod
    def select_fields(cls):
        pass

    @classmethod
    def pydantic_to_postgres_type(t):
        """fill me in"""
        type_mapping = {
            str: "VARCHAR",
            int: "INTEGER",
            float: "FLOAT",
            bool: "BOOLEAN",
            dict: "JSON",
            UUID: "UUID",
        }
        return type_mapping.get(t, "TEXT")

    @classmethod
    def _create_embedding_table_script(cls, entity_model, existing_columns=None):
        """for a separate embedding table
        if we have the connection we can check for a diff and create an alter statement, otherwise we must to the update
        we do not remove columns, but we can add
        """
        pass

    @classmethod
    def _create_view_script(cls, entity_model):
        """
        create or alter the view to select all columns from the join possibly with system columns
        """
        pass

    def create_script(cls, embeddings_inline: bool = True, connection=None):
        """

        (WIP) generate tables for entities -> short term we do a single table with now schema management
        then we will add basic migrations and split out the embeddings + add system fields
        we also need to add the other embedding types - if we do async process we need a metadata server
        we also assume the schema exists for now

        We will want to create embedding tables separately and add a view that joins them
        This creates a transaction of three scripts that we create for every entity
        We should add the created at and updated at system fields and maybe a deleted one

        - key register trigger -> upsert into type-name -> on-conflict do nothing

        - we can check existing columns and use an alter to add new ones if the table exists

        """
        entity_model = cls.model

        def is_optional(field):
            return typing.get_origin(field) is typing.Union and type(
                None
            ) in typing.get_args(field)

        # assert config has the stuff we need

        table_name = (
            f"{entity_model.get_model_namespace()}.{entity_model.get_model_name()}"
        )
        fields = typing.get_type_hints(entity_model)
        field_descriptions = entity_model.model_fields
        id_field = "id"  # <- the id is a hash of the name or a unique id and we use it as the constrain by convention

        columns = []
        for field_name, field_type in fields.items():
            """handle uuid option"""
            if typing.get_origin(
                field_type
            ) is typing.Union and UUID in typing.get_args(field_type):
                postgres_type = "UUID"
            else:
                postgres_type = SqlHelper.pydantic_to_postgres_type(field_type)

            field_desc = field_descriptions[field_name]
            column_definition = f"{field_name} {postgres_type}"
            # we could have a default thing but hold
            # if field_desc.field_info.default is not None:
            #     column_definition += f" DEFAULT {json.dumps(field_desc.field_info.default)}"
            if field_name == id_field:
                column_definition += " PRIMARY KEY "
            elif not is_optional(field_desc):
                column_definition += " NOT NULL"
            columns.append(column_definition)

            """check should add embedding vector for any columns"""
            metadata = field_descriptions.get(field_name)
            extras = getattr(metadata, "json_schema_extra", {}) or {}
            if extras.get("embedding_provider", "").replace("_", "") == "openai":
                columns.append(
                    f"{field_name}_embedding vector({EMBEDDING_LENGTH_OPEN_AI}) NULL"
                )

            """add system fields - created at and updated at fields"""
            # TODO

        columns_str = ",\n    ".join(columns)
        create_table_script = f"""
        CREATE TABLE {table_name} (
            {columns_str}
        );
        """
        return create_table_script
