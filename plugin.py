#
# plugin.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import tornado.web
import os
import json


class BybPluginUIModule(tornado.web.UIModule):
    """
    Class for all UIModules (see tornado docs) that will be used by byb.

    This class will be instantiated by the tornado webserver for every plugin
    to build the website from a template and send it to the client.
    Afterwards this instance will be destructed.

    To make this class adapt to different plugins, the `render` method
    receives a parameterization dict. It includes the location of the plugin's
    root directory. From there, the html and multiple css and js files are
    loaded. Additionally, the parameterization includes values that are then
    used in the plugin with the template system known from tornado.
    """
    # TODO: fix the absolute path restriction for js and css

    def embedded_css(self):
        css_files = [os.path.join(self.plugin_dir, f) for f in self.settings["css_styles"]]
        return None if not css_files else "\n".join([open(css_file).read() for css_file in css_files])

    # def css_files(self):
    #     TODO: Would be nice to include files but I can't give absolute paths to the browser.
    #     # this returns the absolute path which doesn't help
    #     return [os.path.join(self.plugin_dir, f) for f in self.settings["css_styles"]]

    def embedded_javascript(self):
        js_files = [os.path.join(self.plugin_dir, f) for f in self.settings["js_scripts"]]
        # TODO: Put all scripts into a namespace with a variable name that holds the plugin's name?
        return None if not js_files else "\n".join([open(js_file).read() for js_file in js_files])

    def render(self, parameterization):
        """ Keep it like this or subclass to apply options to the render_string method. """
        values = parameterization["values"]
        plugin_name = parameterization["plugin_name"]
        self.plugin_dir = parameterization["plugin_dir"]
        settings_file = os.path.join(self.plugin_dir, "settings.json")
        with open(settings_file) as f:
            self.settings = json.load(f)

        html_template = os.path.join(self.plugin_dir, self.settings["html_template"])
        return self.render_string(html_template, values=values, plugin_name=plugin_name)


class BybPlugin:
    """
    Base class for all plugins of the system.

    Subclass this class to develop plugins for the system. The plugin manager will
    instantiate plugins based on the configuration files and a plugin instance will
    live throughout the lifetime of the server.
    """

    def __init__(self, name, settings, server):
        self._settings = settings
        self._server = server
        self.name = name

    def message_from_client(self, data):
        """
        Received a message from a client.

        Parameters
        ----------
        data: dict
            The messages are sent as strings over websocket but the server takes care
            of parsing the json strings into dicts before handing them over to plugins.
        """
        raise NotImplementedError("message_from_client is not implemented.")

    def send_to_clients(self, data):
        """
        Will send the given data to all clients.

        Parameters
        ----------
        data: dict (json serializable)
            The message that is sent over the websocket will be a string and the server
            takes care of converting any objects to a json string.
        """
        self._server.send_to_clients(data, self.name)

    def will_shutdown(self):
        """
        Called before the plugin's instance is terminated. Might want to do cleanup
        work or send a message to all remaining frontends.
        """
        pass

    def calc_render_data(self):
        return None
