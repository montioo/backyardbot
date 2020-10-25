#
# plugin_main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import os
from plugin import BybPluginUIModule, BybPlugin


class TimetablePlugin(BybPlugin):
    """
    Plugin implementation. Can do useful things like altering the database or
    almost nothing like this example demonstrates.
    """
    def __init__(self, server, name):
        super().__init__(name, server)

    def message_from_client(self, data):
        print("timetable plugin has received a message:")
        print(data)
        self.send_to_clients({"value": 24})
