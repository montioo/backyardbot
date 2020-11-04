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


class EventPluginBase:
    """ Lightweight dummy plugin for event testing. """

    def __init__(self):
        self._should_shutdown = False
        self.update_event = asyncio.Event()
        self.next_return_time = None
        self.message_queue = []

    def subclassable_event_loop(self, msg):
        # TODO: fix ugly name
        """ To be overridden by the user. """
        print("Now handling a message with user-defined code:", msg)
        time.sleep(1.5)

    async def initialize(self):
        """ Initialize function to override. """
        rate = 1/5  # Hz
        while await self.spin_once(rate):
            print("~~ periodic important task ~~")

    async def event_wait(self, evt, timeout):
        # wait for: ( event_triggered  or  time_up )
        try:
            await asyncio.wait_for(evt.wait(), timeout)
        except asyncio.TimeoutError:
            pass
        return evt.is_set()

    async def spin_once(self, rate):

        if self.next_return_time is None:
            self.next_return_time = time.time()
            return True
        self.next_return_time = max(self.next_return_time + 1/rate, time.time())

        while True:
            sleep_time = max(0, self.next_return_time - time.time())
            by_event = await self.event_wait(self.update_event, sleep_time)

            if not by_event:
                return True

            self.update_event.clear()

            if self._should_shutdown:
                print("--> plugin {}.{} exiting".format(__name__, self.__class__.__name__))
                return False

            msg = self.message_queue.pop()
            self.subclassable_event_loop(msg)
            print("Done with msg handling.")


    def receive_message(self, msg):
        self.message_queue.append(msg)
        self.update_event.set()

    def shutdown(self):
        self._should_shutdown = True
        self.update_event.set()


class EventPlugin(EventPluginBase):
    pass


async def main():

    ep = EventPlugin()

    async def sender():
        await asyncio.sleep(7)
        ep.receive_message("hello world")
        print("placed msg")
        await asyncio.sleep(16)
        print("sender done")

    ep_task = asyncio.create_task(ep.initialize())

    await sender()
    await asyncio.sleep(10)

    ep.shutdown()

    await ep_task


if __name__ == "__main__":
    asyncio.run(main())

