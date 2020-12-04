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

        self.logger.info(f"created plugin {self.name}")

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

    def set_localization_data(self, server_settings):
        """ Plugin's localization data consists of global setting and the
        ones given to the plugin. """
        self.localization = pick_localization(self.settings, server_settings)


    # === Websocket Interface ===

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
        topic = f"websocket/{self.name}/frontend"
        message = WebsocketRequest(topic, payload=data, ws_id=ws_id)
        Topics.send_message(message)

    # === Frontend ===

    def render(self, *args, **kwargs):
        # TODO: Debug parameter to reload files every time
        plugin_template_str = open(self.html_template_path).read()
        t = Template(plugin_template_str)
        # TODO: Standard parameters with leading underscore
        # TODO: Integrate data from self.calc_render_data() and kwargs
        return t.render(plugin_name=self.name, values=self.calc_render_data(), localization=self.localization)

    def css_files(self):
        return self.css_file_paths

    def js_files(self):
        return self.js_file_paths

    def calc_render_data(self):
        return None