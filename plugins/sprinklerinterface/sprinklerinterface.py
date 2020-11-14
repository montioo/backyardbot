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
from plugins.sprinklerinterface.gardena_six_way import SixWayActuator

actuator_implementations = {
    "SixWayActuator": SixWayActuator
}


@dataclass
class WateringTask:
    zone: int = 0       # .zone = 0: water all zones
    duration: int = 0   # .duration = 0: use cooldown duration

    def __repr__(self):
        return f"({self.zone}, {self.duration})"


class WateringPlugin(Plugin):
    """
    Tasks of this Plugin:
    - Take lists of zones and durations and call actuators
    - asyncio events to start/stop watering and no loops with sleep(1)
    """

    def initialize(self, settings):
        self.register_topic_callback(TOPIC_START_WATERING, self.start_watering_callback)
        self.actuators = []

    async def start_watering_callback(self, msg):
        """ Immediately hands the watering tasks to the responsible actuators. """
        data = msg.payload
        zones, channels = data["zones"], data["channels"]
        tasks = map(lambda t: WateringTask(t[0], t[1]), zip(zones, channels))

        # dict that maps from multiple zones to the same list for an actuator
        task_mapping = {}
        for actuator in self.actuators:
            new_task_list = []
            for zone in actuator.managed_zones:
                task_mapping[zone] = new_task_list

        # append task to the list of tasks of the responsible actuator
        for task in tasks:
            if task.zone in task_mapping.keys():
                task_mapping[task.zone].append(task)
            else:
                self.logger.warn(f"Received task for unknown zone: {task}")

        # hand collected task lists to actuators
        for actuator in self.actuators:
            new_task_list = task_mapping[actuator.managed_zones[0]]
            actuator.start_watering(new_task_list)

    # === Actuator and Zone Setup ===

    def _initialize_actuators(self):
        for actuator_config in self.settings["plugin_settings"]["actuators"]:
            actuator_class = actuator_config.get("python_class", None)
            if actuator_class not in actuator_implementations:
                self.logger.warning(f"{actuator_class} is not in the list of known implementations")
                continue

            managed_zones = actuator_config.get("zones", [])
            if not managed_zones:
                self.logger.warn(f"Managed zones for {actuator_class} instance are empty!")
                continue

            name = None
            actuator_specific_settings = actuator_config.get("actuator_specific_settings", {})
            actuator = actuator_implementations[actuator_class](managed_zones, name, actuator_specific_settings)
            self.actuators.append(actuator)
