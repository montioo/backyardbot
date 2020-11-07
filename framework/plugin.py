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
import time
import asyncio
import inspect
from jinja2 import Template
from collections import deque
from .event import EventComponent
from .utility import pick_localization, create_logger
from .communication import Topics, WebsocketRequest


class Plugin(EventComponent):
    """
    Base class for all plugins of the system.

    Subclass this class to develop plugins. The plugin manager will
    instantiate plugins based on the configuration files and a plugin
    instance will live throughout the lifetime of the server.
    """

    def __init__(self, name, plugin_settings_path):
        settings = json.load(open(plugin_settings_path))
        super().__init__(settings)
        self.settings = settings

        plugin_dir = os.path.dirname(plugin_settings_path)

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
        """ To be overridden by subclasses to do any setup. """
        pass


    # === Public Methods ===
    # === -------------- ===

    # === Websocket Interface ===

    def set_localization_data(self, global_settings):
        self.localization_data = pick_localization(self.settings, global_settings)

    def register_server(self, server):
        """
        Deprecated?

        Is called by the server so that the plugin knows the server instance to:
        - Send messages over websockets to the js frontends.
        - Get merged localization data from server and plugin config.
        """
        # TODO: Is this still needed? Communication happens via topics but how to query website renderings from plugins?
        self._server = server
        self.localization_data = pick_localization(self.settings, self._server.settings)

    # async def message_from_client(self, data):
    #     """
    #     Received a message from a client.

    #     Parameters
    #     ----------
    #     data: dict
    #         The messages are sent as strings over websocket but the server
    #         takes care of parsing the json strings into dicts before handing
    #         them over to plugins.
    #     """
    #     raise NotImplementedError("message_from_client is not implemented.")

    async def send_to_clients(self, data, ws_id=-1):
        """
        Deprecated. (soon)

        Will send the given data to all clients.

        Parameters
        ----------
        data: dict (json serializable)
            The message that is sent over the websocket will be a string and
            the server takes care of converting any objects to a json string.
        """
        # TODO: Replace this. The server should listen to `websocket/<plugin_name>/frontend topics`
        # await self._server.send_to_clients(data, self.name)
        topic = "websocket/{}/frontend".format(self.name)
        message = WebsocketRequest(topic, payload=data, ws_id=ws_id)
        Topics.send_message(message)

    # === Frontend ===

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

    def calc_render_data(self):
        return None

    # === Deprecated ===
    # === ---------- ===

    def will_shutdown(self):
        """
        Called before the plugin's instance is terminated. Might want to do
        cleanup work or send a message to all remaining frontends.
        """
        pass
