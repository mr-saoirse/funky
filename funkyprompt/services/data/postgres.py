from funkyprompt.core import AbstractModel
import typing
from funkyprompt.services.data import DataServiceBase
import psycopg2
from funkyprompt.core.utils.env import POSTGRES_CONNECTION_STRING
from funkyprompt.core.utils import logger


class PostgresService(DataServiceBase):
    """the postgres service wrapper for sinking and querying entities/models"""

    def __init__(self, model: AbstractModel):
        self.conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        self.model = model

    def _alter_model(cls):
        """try to alter the table by adding new columns only"""
        raise NotImplementedError("alter table not yet implemented")

    def _create_model(cls):
        """internal create model"""

        try:
            script = cls.model.sql().create_script()
            logger.debug(script)
            cls.execute(script)
            logger.info(f"updated {cls.model.get_model_fullname()}")
        except Exception as pex:
            if pex is psycopg2.errors.DuplicateTable:
                cls._alter_model()
            else:
                raise

    def __drop_table__(cls):
        """drop the table - really just for testing and not something we would likely do often"""
        script = f"drop table {cls.model.get_model_fullname()}"
        logger.debug(script)
        cls.execute(script)
        logger.info(f"dropped {cls.model.get_model_fullname()}")

    def execute(cls, query: str, data: tuple = None):
        """run any sql query
        this works only for selects and transactional updates without selects
        """
        try:
            c = cls.conn.cursor()
            c.execute(query, data)

            if c.description:
                result = c.fetchall()
                cls.conn.commit()
                column_names = [desc[0] for desc in c.description or []]
                result = [dict(zip(column_names, r)) for r in result]
                return result
            """case of upsert transactions"""
            cls.conn.commit()
        except Exception as pex:
            cls.conn.rollback()
            raise
        finally:
            cls.conn.close

    def execute_upsert(cls, query: str, data: tuple = None, page_size: int = 100):
        """run an upsert sql query"""
        try:

            c = cls.conn.cursor()
            psycopg2.extras.execute_values(
                c, query, data, template=None, page_size=page_size
            )

            if c.description:
                result = c.fetchall()
                cls.conn.commit()
                column_names = [desc[0] for desc in c.description or []]
                result = [dict(zip(column_names, r)) for r in result]
                return result
        except Exception as pex:
            cls.conn.rollback()
            raise
        finally:
            cls.conn.close

    @classmethod
    def create_model(cls, model: AbstractModel):
        """creates the model based on the type.
        system fields are added for created and updated at.
        the raw table is associated with separate embeddings table via a view
        """
        return cls(model)._create_model()

    def update_records(self, records: typing.List[AbstractModel]):
        """records are updated using typed object relational mapping.
        the embedding update is queued
        """
        if records and not isinstance(records, list):
            records = [records]
        helper = self.model.sql()
        if records:
            query = helper.upsert_query(batch_size=len(records))
            result = self.execute_upsert(
                query=query,
                data=(
                    [
                        tuple(helper.serialize_for_db(r).values())
                        for i, r in enumerate(records)
                    ]
                ),
            )

            self.queue_update_embeddings(result)

            return result

    def queue_update_embeddings(self, result: typing.List[dict]):
        """embeddings in general should be processed async
        when we insert some data, we read back a result with ids and column data for embeddings
        we then use whatever provided to get an embedding tensor and save it to the database
        this insert could be inline or adjacent table
        """
        from funkyprompt.core.utils.embeddings import embed_frame

        helper = self.model.sql()

        embeddings = embed_frame(
            result,
            field_mapping=self.model.get_embedding_fields(),
            id_column=helper.id_field,
        )

        query = helper.embedding_fields_partial_update_query(batch_size=len(result))

        return self.execute_upsert(
            query=query, data=(helper.partial_model_tuple(e) for e in embeddings)
        )

    def select_one(self, name: str):
        """a convenience to sample a single object by name (could also be id but not as friendly)"""
        query = self.model.sql().select_query() + " WHERE name = %s"
        return self.execute(query, data=(name,))

    def ask(self, question: str):
        """natural language to SQL is used to query the store"""
        # prompt  = self.model.get_model_as_prompt()
        query = self.model.sql().natural_to_sql(question)
        return self.execute(query)

    def query(self, query: str):
        """
        directly query by SQL/alias execute but actually this could be a more general multimodel type query

        LOAD 'age';

        """
        return self.execute(query)


"""notes


"""
