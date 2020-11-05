#
# event.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

"""
Requirements:
- A plugin should wait for messages. But not simply by checking every second
  but because an asyncio event object will be released.
  => Using asyncio events
- How to deal with timed stuff?
  => using asyncio.wait_for to wait for events with a timeout
"""

import asyncio
import time
import inspect



class EventPluginBase:
    """ Lightweight dummy plugin for event testing. """

    def __init__(self):
        self._should_shutdown = False
        self.update_event = asyncio.Event()
        self.next_return_time = None
        self.message_queue = []
        self.message_handlers = {}

    def initialize(self):
        """ To be overridden by subclasses to do any necessary
        initialization. """
        pass

    async def event_loop(self):
        """
        May be overridden by subclasses if custom periodic tasks should be handled
        by the plugin, e.g. reading an external sensor every 10 seconds. Example usage:
        ```
        rate = 1/10  # 0.1 Hz = executed every 10 seconds
        while await self.spin_once(rate):
            print("Important periodic task here.")
        ```
        """
        await self.spin()

    async def event_wait(self, evt, timeout):
        # wait for: ( event_triggered  or  time_up )
        try:
            await asyncio.wait_for(evt.wait(), timeout)
        except asyncio.TimeoutError:
            pass
        return evt.is_set()

    def _ramining_time(self, rate):
        if rate is None:
            return None
        t = time.time()

        if self.next_return_time is None:
            self.next_return_time = t

        if t > self.next_return_time:
            self.next_return_time = max(self.next_return_time + 1/rate, t)

        return self.next_return_time - t

    async def spin_once(self, rate):
        """
        Plugin's task handling. Will try to return on time so that code can
        be executed with a frequency given by `rate`. Returns `False` if the
        plugin received a signal to shut down. `spin_once(..)` will not do any
        computations itself if all topic callbacks are asynchronous
        functions.
        """
        # TODO: Deal with rate = None for no timeout

        # if self.next_return_time is None:
        #     self.next_return_time = time.time()
        #     return True
        # self.next_return_time = max(self.next_return_time + 1/rate, time.time())

        while True:
            # sleep_time = max(0, self.next_return_time - time.time())
            sleep_time = self._ramining_time(rate)
            by_event = await self.event_wait(self.update_event, sleep_time)

            if not by_event:
                return True

            self.update_event.clear()

            if self._should_shutdown:
                print("--> plugin {}.{} exiting".format(__name__, self.__class__.__name__))
                return False

            # Execute callback for longest waiting message
            msg = self.message_queue.pop()
            topic, payload = msg["topic"], msg.get("payload", None)
            callback = self.message_handlers.get(topic, None)
            if callback is None:
                print("No callback available for message in topic {}".format(topic))
            elif inspect.iscoroutinefunction(callback):
                # launch asynchronously and return immediately
                asyncio.ensure_future(callback(payload))
            else:
                callback(payload)

            print("Done with msg handling.")

    async def spin(self):
        """
        Will not return until the plugin receives the command to shut down.
        It's important that `await self.spin()` is called in the event loop
        as it enables the plugin to handle messages with its defined
        callbacks.
        """
        await self.spin_once(None)

    def register_topic_callback(self, topic_name, callback):
        """
        Registers a callback function that will be called once the plugin
        receives a message on the given topic. `callback` may be a
        synchronous or asynchronous function (a coroutine defined with async
        def ...).
        Topic name 'websocket' is reserved for messages that are received by
        the server over a websocket connection.
        """
        # TODO: use register_topic_callback for websocket messages as well.
        self.message_handlers[topic_name] = callback

    def receive_message(self, msg):
        self.message_queue.append(msg)
        self.update_event.set()

    def shutdown(self):
        self._should_shutdown = True
        self.update_event.set()

