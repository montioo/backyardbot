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


class TimetableUIModule(BybPluginUIModule):
    """ A subclass of BybPluginUIModule needs to be created for every plugin. """
    def __init__(self, handler):
        # An instance of this class uses the directory of the plugin to get html, css and js files
        plugin_dir = os.path.dirname(os.path.realpath(__file__))
        super().__init__(handler, plugin_dir)


class TimetablePlugin(BybPlugin):
    """
    Plugin implementation. Can do useful things like altering the database or
    almost nothing like this example demonstrates.
    """
    def __init__(self, server, name):
        super().__init__(name, server)
        self.ui_module = TimetableUIModule

    def message_from_client(self, data):
        print("timetable plugin has received a message:")
        print(data)
        self.send_to_clients({"value": 24})
