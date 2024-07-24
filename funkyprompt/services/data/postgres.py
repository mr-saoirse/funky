from funkyprompt.core import AbstractModel
import typing
from funkyprompt.services.data import DataServiceBase


class PostgresService(DataServiceBase):
    """the postgres service wrapper for sinking and querying entities/models"""

    def create_model(self, model: AbstractModel):
        """creates the model based on the type.
        system fields are added for created and updated at.
        the raw table is associated with separate embeddings table via a view
        """
        pass

    def update_records(self, records: typing.List[AbstractModel]):
        """records are updated using typed object relational mapping.
        the embedding update is queued
        """
        pass

    def select_one(self, id: str):
        """a convenience to sample a single object by id"""
        pass

    def ask(self, question: str):
        """natural language to SQL is used to query the store"""
        pass

    def query(self, query: str):
        """
        directly query by SQL
        """
        pass
