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
from framework.utility import pick_localization, create_logger


class Plugin:
    """
    Base class for all plugins of the system.

    Subclass this class to develop plugins. The plugin manager will
    instantiate plugins based on the configuration files and a plugin
    instance will live throughout the lifetime of the server.
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

        self._should_shutdown = False
        self._received_update_event = asyncio.Event()
        self._next_return_time = None
        self._message_queue = deque()
        self._message_handlers = {}

        self.initialize(self.settings)

    def initialize(self, settings: dict):
        """ To be overridden by subclasses to do any setup. """
        pass


    # === Public Methods ===
    # === -------------- ===

    # === Event handling ===

    async def event_loop(self):
        """
        Asynchronous event loop for the plugin to run recurring tasks. Is
        called once as the server starts and may be overridden by subclasses
        if custom periodic tasks should be handled by the plugin, e.g.
        reading an external sensor every 10 seconds. Example usage:
        ```
        rate = 1/10  # 0.1 Hz = executed every 10 seconds
        while await self.spin_once(rate):
            print("Important periodic task here.")
        ```
        """
        await self.spin()

    async def spin_once(self, rate):
        """
        Plugin's task handling. Will try to return on time so that code can
        be executed with a frequency given by `rate`. Returns `False` if the
        plugin received a signal to shut down. `spin_once(..)` will not do any
        computations itself if all topic callbacks are asynchronous
        functions.
        """
        while True:
            by_event = await self._event_wait(self._received_update_event, self.remaining_time(rate))

            if not by_event:
                return True

            self._received_update_event.clear()

            if self._should_shutdown:
                self.logger.info("--> plugin {}.{} exiting".format(__name__, self.__class__.__name__))
                return False

            # Execute callback for longest waiting message
            msg = self._message_queue.popleft()
            topic, payload = msg.topic, msg.payload
            callback = self._message_handlers[topic]
            if callback is None:
                self.logger.info("No callback available for message in topic {}".format(topic))
            elif inspect.iscoroutinefunction(callback):
                # launch asynchronously and return immediately
                asyncio.ensure_future(callback(payload))
            else:
                self.logger.warning("Using synchronous callback function.")
                callback(payload)

    async def spin(self):
        """
        Will not return until the plugin receives the command to shut down.
        It's important that `await self.spin()` is called in the event loop
        as it enables the plugin to handle messages with its defined
        callbacks.
        """
        await self.spin_once(None)
    # TODO: while_system_active condition for graceful shutdown: https://docs.python.org/3.8/library/signal.html

    # === Messaging ===

    def register_topic_callback(self, topic_name, callback):
        """
        Registers a callback function that will be called once the plugin
        receives a message on the given topic. `callback` may be a
        synchronous or (preferably) asynchronous function (a coroutine
        defined with async def ...).
        There are several reserved topic names:
        - websocket/<plugin_name>/backend : message from a frontend client to the backend
        - websocket/<plugin_name>/frontend : message from a backend client to the frontend
        - will_shutdown : called before the server shuts down
        """
        self._message_handlers[topic_name] = callback

    def receive_message(self, msg):
        """
        Called by the central communication maintainer to enqueue a message
        into the plugin's message buffer. **Don't** call this method directly
        but send a message to a subscribed topic using the Topic maintainer.
        """
        self._message_queue.append(msg)
        if msg.topic in self._message_handlers.keys():
            self._received_update_event.set()

    # === Websocket Interface ===

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

    async def send_to_clients(self, data):
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
        await self._server.send_to_clients(data, self.name)

    def shutdown(self):
        """ Will stop the plugin's event loop. """
        self._should_shutdown = True
        self._received_update_event.set()

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


    # === Private Methods ===
    # === --------------- ===

    def _remaining_time(self, rate):
        if rate is None:
            return None
        t = time.time()

        if self._next_return_time is None:
            self._next_return_time = t

        if t > self._next_return_time:
            self._next_return_time = max(self._next_return_time + 1/rate, t)

        return self._next_return_time - t

    async def _event_wait(self, evt, timeout):
        # wait for: ( event_triggered  or  time_up )
        try:
            await asyncio.wait_for(evt.wait(), timeout)
        except asyncio.TimeoutError:
            pass
        return evt.is_set()


    # === Deprecated ===
    # === ---------- ===

    def new_client(self):
        # TODO: This should be called very time a new client connects.
        # Benefit: All relevant data for the new client could also be included in
        #  the html render. But maybe the old clients need the be updated as well.
        pass

    def will_shutdown(self):
        """
        Called before the plugin's instance is terminated. Might want to do
        cleanup work or send a message to all remaining frontends.
        """
        pass
