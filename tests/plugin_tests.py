#
# plugin_tests.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import time
from framework.event import EventPluginBase
import asyncio
import unittest


start_time = time.time()
og_print = print
print_list = []

def time_print(*args, **kwargs):
    global start_time, print_list
    delta_time = time.time() - start_time
    # og_print(round(delta_time, 2), *args, **kwargs)
    print_list.append((round(delta_time, 2), args[0]))

print = time_print


class EventPluginToTest(EventPluginBase):

    def initialize(self):
        self.register_topic_callback("example_topic", self.message_callback)

    async def message_callback(self, msg):
        """ To be overridden by the user. """
        print(f"+++ start callback for msg {msg}")
        await asyncio.sleep(5)
        print("--- done with callback")

    async def event_loop(self):
        rate = 1/5  # 0.2 Hz = executed every 5 seconds
        while await self.spin_once(rate):
            print("~~ important periodic task here. ~~")


async def main():

    ep = EventPluginToTest()
    ep.initialize()

    async def sender():
        await asyncio.sleep(7)
        ep.receive_message({"topic": "example_topic", "payload": "hello world"})
        print("placed msg")
        await asyncio.sleep(6)
        print("sender done")

    ep_task = asyncio.create_task(ep.event_loop())

    await sender()
    await asyncio.sleep(5)

    print("sending shutdown signal to plugin")
    ep.shutdown()

    await ep_task


class TestPluginEventSystem(unittest.TestCase):

    def setUp(self):
        global print_list
        print_list = []
        self.ep = EventPluginToTest()
        self.ep.initialize()

    def tearDown(self):
        pass

    def test_async_spin_and_msg(self):
        """
        Will initialize a plugin, set an asynchronous callback for messages
        and check that the execution timing for both event loop and message
        callback work as expected.
        """
        asyncio.run(main())
        ref = [
            (0.0, "~~ important periodic task here. ~~"),
            (5.01, "~~ important periodic task here. ~~"),
            (7.01, "placed msg"),
            # (None, "Done with msg handling."),
            (7.01, "+++ start callback for msg hello world"),
            (10.01, "~~ important periodic task here. ~~"),
            (12.01, "--- done with callback"),
            (13.01, "sender done"),
            (15.0, "~~ important periodic task here. ~~"),
            (18.01, "sending shutdown signal to plugin"),
            # (None, "--> plugin framework.event.EventPluginToTest exiting")
        ]
        global print_list
        times_ref, str_ref = zip(*ref)
        times_out, str_out = zip(*print_list)
        self.assertEqual(list(str_ref), list(str_out))
        # almostEqual for collection types only available in np
        for time_ref, time_out in zip(times_ref, times_out):
            self.assertAlmostEqual(time_ref, time_out, places=1)


if __name__ == "__main__":
    unittest.main()
