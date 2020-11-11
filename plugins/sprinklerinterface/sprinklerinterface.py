#
# sprinklerinterface.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
from byb.byb_common import TOPIC_START_WATERING

from dataclasses import dataclass


@dataclass
class WateringTask:
    zone: int = 0       # .zone = 0: water all zones
    duration: int = 0   # .duration = 0: use cooldown duration

    def __repr__(self):
        return "({}, {})".format(self.zone, self.duration)


class WateringPlugin(Plugin):
    """
    Tasks of this Plugin:
    - Take lists of zones and durations and call actuators
    - asyncio events to start/stop watering and no loops with sleep(1)
    """

    def initialize(self, settings):

        self.register_topic_callback(TOPIC_START_WATERING, self.start_watering_callback)

        actuator_1, actuator_2 = None, None

        self.zone_mapping = {
            1: actuator_1,
            2: actuator_2,
            3: actuator_2,
            4: actuator_2
        }

    async def start_watering_callback(self, msg):
        """ Immediately hands the watering tasks to the responsible actuators. """
        data = msg.payload
        zones, channels = data["zones"], data["channels"]
        tasks = map(lambda t: WateringTask(t[0], t[1]), zip(zones, channels))
        for task in tasks:
            if task.zone in self.zone_mapping.keys():
                self.zone_mapping[task.zone].start_watering(task)
