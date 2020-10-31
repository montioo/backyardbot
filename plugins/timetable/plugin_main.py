#
# plugin_main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import os
from framework.plugin import Plugin
from framework.memory import Database


# TODO: Define somewhere else so that other plugins can access this.
TIMETABLE_DB = "time_schedule_table"


class TimetablePlugin(Plugin):
    """
    Plugin implementation. Can do useful things like altering the database or
    almost nothing like this example demonstrates.
    """

    def initialize(self, settings):
        self.msg_handlers = {
            "add_entries": self.handle_add_entries,
            "remove_entry": self.handle_remove_entry
        }

        self.tt_db = Database.get_db_for(TIMETABLE_DB)

    async def message_from_client(self, data):
        print("timetable plugin has received a message:")

        for action in data.keys():
            if action in self.msg_handlers:
                await self.msg_handlers[action](data[action])
            else:
                print("received unknown action:", action)

    async def handle_add_entries(self, new_entries):
        # receive and entry that should be added to the DB
        # 1. add entry to db (which will also assign an ID to that entry)
        # 2. send msg to clients with updated watering list

        # TODO: Make sure that the data is valid
        for entry in new_entries:
            self.tt_db.insert(entry)
        await self.send_updated_table()

    async def handle_remove_entry(self, data):
        print("-------> received remove command", type(data))
        doc_id_to_remove = data
        print("-------> going to remove", doc_id_to_remove)
        self.tt_db.remove(doc_ids=[doc_id_to_remove])
        await self.send_updated_table()


    async def send_updated_table(self):
        all_entries = self.get_all_entries()
        # sort entries by day and insert spacers
        all_entries.sort(key = lambda e: (e["weekday"], 60*e["time_hh"] + e["time_mm"], e["duration"], e["zones"][0]))
        await self.send_to_clients(all_entries)

    def get_all_entries(self):
        return Database.as_dict_with_id(self.tt_db.all())


    ### demo / debug

    def query_db_for_timetable(self):
        """
        The json serializable object that is returned here, will be available
        in the variable `values` in the html template of this plugin.
        """

        # TODO: Would prefer async execution for all DB related things
        return {
            "channels": [1, 2, 3, 4, 5],  # TODO: Get those from another DB as well
            "timetable": self.get_all_entries()
        }

    def calc_render_data(self):
        # Not sure if I will use this. Seems like double the work.
        # I mean at least don't use it for not for DB related data.
        return self.query_db_for_timetable()

    def new_client(self):
        self.send_to_clients(self.query_db_for_timetable())