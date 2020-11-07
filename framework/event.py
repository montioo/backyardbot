#
# event.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#


import asyncio
import time
import inspect
from collections import deque
from .utility import create_logger
from .communication import Topics


class EventComponent:
    """
    Base class for all components of the system that want to send or receive
    messages with asynchronous callbacks.
    """

    def __init__(self, settings):
        logger_name = __name__ + "." + self.__class__.__name__
        # TODO: Make the global config already available here.?
        self.logger = create_logger(logger_name, settings)

        self._should_shutdown = False
        self._received_update_event = asyncio.Event()
        self._next_return_time = None
        self._message_queue = deque()
        self._message_handlers = {}

        Topics.register(self)

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
            self.logger.info("Important periodic task here.")
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
            by_event = await self._event_wait(self._received_update_event, self._remaining_time(rate))

            if not by_event:
                return True

            self._received_update_event.clear()

            if self._should_shutdown:
                self.logger.info("--> plugin {}.{} exiting".format(__name__, self.__class__.__name__))
                return False

            # Execute callback for longest waiting message
            msg = self._message_queue.popleft()
            callback = self._message_handlers[msg.topic]
            if inspect.iscoroutinefunction(callback):
                # launch asynchronously and return immediately
                asyncio.ensure_future(callback(msg))
            else:
                # for quick tasks, a synchronous callback is fine
                # self.logger.warning("Using synchronous callback function.")
                callback(msg)

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
        if msg.topic in self._message_handlers.keys():
            self._message_queue.append(msg)
            self._received_update_event.set()

    def shutdown(self):
        """ Will stop the plugin's event loop. """
        self._should_shutdown = True
        self._received_update_event.set()


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
