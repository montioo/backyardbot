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
