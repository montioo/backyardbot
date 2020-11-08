#
# memory.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from tinydb import TinyDB


class Database:
    """
    Serves as storage for data that might change often as well as data that is mostly
    consistent, compiled by one entity and nontheless of interest for other entities.
    """
    db = None

    @classmethod
    def set_db_path(cls, path):
        cls.db = TinyDB(path)

    @classmethod
    def get_db_for(cls, name):
        return cls.db.table(name)

    @classmethod
    def as_dict_with_id(cls, query_result, id_tag="doc_id"):
        # from Python 3.9 on: dict(e) | {"id": e.doc_id}
        return [{**dict(e), **{id_tag: e.doc_id}} for e in query_result]

    @classmethod
    def set_table_update_hook(cls, table_name):
        # TODO: Send a message on a topic as the table is updated.
        # Structure: "database_update/<table_name>"
        raise NotImplementedError("Table update hooks not implemented yet.")

