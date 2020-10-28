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
import uuid


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

    # TODO: make the parameterization include lists of **all** css and js files
    #   that all plugins need as they will only be included once per UIModule.

    # def embedded_css(self):
    #     # css_files = [os.path.join(self.plugin_dir, f) for f in self.settings["css_styles"]]
    #     return None if not self.css_filelist else "\n".join([open(css_file).read() for css_file in self.css_filelist])

    def css_files(self):
        # TODO: Would be nice to include files but I can't give absolute paths to the browser.
        # this returns the absolute path which doesn't help
        ln = len("/Users/monti/Documents/ProjectsGit/byb-github")
        return [cssf[ln:] for cssf in self.css_filelist]

    # def embedded_javascript(self):
    #     # js_files = [os.path.join(self.plugin_dir, f) for f in self.settings["js_scripts"]]
    #     # TODO: Put all scripts into a namespace with a variable name that holds the plugin's name?
    #     # return None if not js_files else "\n".join([open(js_file).read() for js_file in js_files])
    #     return None if not self.js_filelist else "\n".join([open(js_file).read() for js_file in self.js_filelist])

    def javascript_files(self):
        # **don't** use this path with trailing slash. Then the shortened js files will not have a
        #  leading space which will cause tornado to do annoying things (i.e. not work).
        # TODO: Removing the leading part of the directory can be done in the plugin manager.
        ln = len("/Users/monti/Documents/ProjectsGit/byb-github")
        return [jsf[ln:] for jsf in self.js_filelist]

    def render(self, plugin_info, css_filelist, js_filelist):
        """ Keep it like this or subclass to apply options to the render_string method. """
        self.css_filelist = css_filelist
        self.js_filelist = js_filelist
        values = plugin_info["values"]
        plugin_name = plugin_info["plugin_name"]
        html_template_path = plugin_info["html_template_path"]

        return self.render_string(html_template_path, values=values, plugin_name=plugin_name)


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
        # self.messaging = server.messaging
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


    # TODO: Message handling for topics.
    # Have every plugin run an event loop. Sending a message over a topic will then only
    # consist of putting the message into a plugin's message buffer.
    # The end of the plugin's init method would then need to run code similar to
    # rosnode spin: Keep node alive and check for updates at a certain interval.

