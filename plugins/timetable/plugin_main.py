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


class TimetablePlugin(Plugin):
    """
    Plugin implementation. Can do useful things like altering the database or
    almost nothing like this example demonstrates.
    """

    def message_from_client(self, data):
        print("timetable plugin has received a message:")
        print(data)
        self.send_to_clients({"value": "this is the timetable speaking"})


    ### demo / debug

    def query_db_for_timetable(self):
        """
        The json serializable object that is returned here, will be available
        in the variable `values` in the html template of this plugin.
        """

        # TODO: Would prefer async execution for all DB related things
        return {
            "channels": [1, 2, 3, 4, 5],
            "timetable": [
                {"time": "15:00", "channel": 3, "duration": 560, "day": 7},
                {"time": "19:00", "channel": 1, "duration": 120, "day": 0}
            ]
        }

    def calc_render_data(self):
        # Not sure if I will use this. Seems like double the work.
        # I mean at least don't use it for not for DB related data.
        return self.query_db_for_timetable()

    def new_client(self):
        self.send_to_clients(self.query_db_for_timetable())