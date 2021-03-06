#
# plugin_main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
from framework.memory import Database
from framework.communication import Topics, BaseMessage
from byb.byb_common import TIMETABLE_DB_NAME, ZONE_DB_NAME


class TimetablePlugin(Plugin):
    """
    Plugin implementation. Can do useful things like altering the database or
    almost nothing like this example demonstrates.
    """

    def initialize(self, settings):
        self._command_handlers = {
            "add_entries": self.handle_add_entries,
            "remove_entry": self.handle_remove_entry
        }

        self.tt_db = Database.get_db_for(TIMETABLE_DB_NAME)
        self.zone_db = Database.get_db_for(ZONE_DB_NAME)

        # Registering standard websocket message handler.
        ws_backend_topic = f"websocket/{self.name}/backend"
        self.register_topic_callback(ws_backend_topic, self.ws_message_from_frontend)

        ws_new_client_topic = "websocket/new_client"
        self.register_topic_callback(ws_new_client_topic, self.new_ws_client)

    async def ws_message_from_frontend(self, msg):
        self.logger.info("timetable plugin has received a message.")
        data = msg.payload

        cmd = data.get("command", None)
        if cmd in self._command_handlers.keys():
            await self._command_handlers[cmd](data.get("payload", None))

    async def handle_add_entries(self, new_entries):
        # receive and entry that should be added to the DB
        # 1. add entry to db (which will also assign an ID to that entry)
        # 2. send msg to clients with updated watering list

        # TODO: Make sure that the data is valid
        for entry in new_entries:
            self.tt_db.insert(entry)

        # tmp solution
        topic = "database_update/" + TIMETABLE_DB_NAME
        msg = BaseMessage(topic)
        Topics.send_message(msg)
        #

        await self.send_updated_table()

    async def handle_remove_entry(self, data):
        doc_id_to_remove = data
        self.logger.info(f"-------> going to remove entry with id {doc_id_to_remove}")
        self.tt_db.remove(doc_ids=[doc_id_to_remove])

        # TODO: tmp solution to raise awareness for DB updates
        topic = "database_update/" + TIMETABLE_DB_NAME
        msg = BaseMessage(topic)
        Topics.send_message(msg)
        #

        await self.send_updated_table()

    async def send_updated_table(self, ws_id=-1):
        all_entries = self.get_all_entries()
        # sort entries by day and insert spacers
        all_entries.sort(key=lambda e: (e["weekday"], 60*e["time_hh"] + e["time_mm"], e["duration"], e["zones"][0]))
        await self.send_to_clients({
            "command": "timetable_contents",
            "payload": all_entries
        }, ws_id=ws_id)

    def get_all_entries(self):
        return Database.as_dict_with_id(self.tt_db.all())

    async def new_ws_client(self, msg):
        await self.send_updated_table(ws_id=msg.ws_id)

    def query_db_for_timetable(self):
        """
        The json serializable object that is returned here, will be available
        in the variable `values` in the html template of this plugin.
        """

        # TODO: Would prefer async execution for all DB related things
        return {
            "zones": [zone["name"] for zone in self.zone_db.all() if "name" in zone],
            "timetable": self.get_all_entries()
        }

    def calc_render_data(self):
        # Not sure if I will use this. Seems like double the work.
        # I mean at least don't use it for not for DB related data.
        return self.query_db_for_timetable()
