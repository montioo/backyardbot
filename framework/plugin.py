#
# plugin.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import os
import json
import uuid
import asyncio
from jinja2 import Template
from framework.utility import pick_localization, create_logger


class Plugin:
    """
    Base class for all plugins of the system.

    Subclass this class to develop plugins. The plugin manager will
    instantiate plugins based on the configuration files and a plugin instance will
    live throughout the lifetime of the server.
    """

    def __init__(self, name, plugin_settings_path):
        self.settings = json.load(open(plugin_settings_path))
        plugin_dir = os.path.dirname(plugin_settings_path)

        logger_name = __name__ + "." + self.__class__.__name__
        # TODO: Make the global config already available here.
        self.logger = create_logger(logger_name, self.settings)

        self.name = plugin_settings_path.split("/")[-2]

        self.logger.info("created plugin {}".format(self.name))

        self.html_template_path = os.path.join(plugin_dir, self.settings["html_template"])
        # TODO: relative paths. Must include leading slash from project's root dir.
        self.css_file_paths = [
            os.path.join(plugin_dir, css_file) for css_file in self.settings.get("css_styles", [])]
        self.js_file_paths = [
            os.path.join(plugin_dir, js_file) for js_file in self.settings.get("js_scripts", [])]

        self.initialize(self.settings)


    def initialize(self, settings: dict):
        """ To be overridden by subclasses. """
        pass

    async def event_loop(self):
        """ Asynchronous event loop for the plugin to run recurring tasks. """
        pass

    async def spin_once(self):
        # TODO: Variable spin duration / rate
        await asyncio.sleep(5)

    async def spin(self):
        # TODO: Is this used with eventhandling or whatever? If not, it's not needed anymore.
        while True:
            await asyncio.sleep(5)

    def register_server(self, server):
        self._server = server
        self.localization_data = pick_localization(self.settings, self._server.settings)

    async def message_from_client(self, data):
        """
        Received a message from a client.

        Parameters
        ----------
        data: dict
            The messages are sent as strings over websocket but the server takes care
            of parsing the json strings into dicts before handing them over to plugins.
        """
        raise NotImplementedError("message_from_client is not implemented.")

    async def send_to_clients(self, data):
        """
        Will send the given data to all clients.

        Parameters
        ----------
        data: dict (json serializable)
            The message that is sent over the websocket will be a string and the server
            takes care of converting any objects to a json string.
        """
        await self._server.send_to_clients(data, self.name)

    def will_shutdown(self):
        """
        Called before the plugin's instance is terminated. Might want to do cleanup
        work or send a message to all remaining frontends.
        """
        pass

    def calc_render_data(self):
        return None

    def new_client(self):
        # TODO: This should be called very time a new client connects.
        # Benefit: All relevant data for the new client could also be included in
        #  the html render. But maybe the old clients need the be updated as well.
        pass

    def render(self, *args, **kwargs):
        # TODO: Debug parameter to reload files every time
        plugin_template_str = open(self.html_template_path).read()
        t = Template(plugin_template_str)
        # TODO: Standard parameters with leading underscore
        # TODO: Integrate data from self.calc_render_data() and kwargs
        return t.render(plugin_name=self.name, values=self.calc_render_data(), localization=self.localization_data)

    def css_files(self):
        return self.css_file_paths

    def js_files(self):
        return self.js_file_paths

    # TODO: Message handling for topics.
    # Have every plugin run an event loop. Sending a message over a topic will then only
    # consist of putting the message into a plugin's message buffer.
    # The end of the plugin's init method would then need to run code similar to
    # rosnode spin: Keep node alive and check for updates at a certain interval.

