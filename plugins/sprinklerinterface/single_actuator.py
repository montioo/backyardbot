#
# single_actuator.py
# backyardbot
#
# Created: Dezember 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from plugins.sprinklerinterface.actuator import ActuatorInterface, WateringTask
from plugins.sprinklerinterface.gpio import DebugGpioInterface, RaspiGpioInterface
from typing import List


class SingleActuator(ActuatorInterface):
    """
    Controls a single actuator, e.g. a pump or a magnetic valve using one
    gpio port. Will start watering as soon as it receives a command and not
    communicate with other actuators. This means, that if five instances of
    this actuator are active at the same time, the waterpressure might drop
    significantly and reach a point where driving a sprinkler is not really
    possible. To have only one actuator active at a time, look the
    MultiActuator class.
    """

    def __init__(self, managed_zones, name, config):
        logger_config = config.get("logging", {})
        super().__init__(managed_zones, name, logger_config)

        self.managed_zone = managed_zones[0]
        self.gpio_pin = config["gpio_pin"]

        if config.get("use_debug_gpio", False):
            self._gpio = DebugGpioInterface([self.gpio_pin], config)
        else:
            self._gpio = RaspiGpioInterface([self.gpio_pin], config)

        # somehow this timing thing is something I'm solving again and again...
        # look at async events.
        self._remaining_duration = 0
        self._watering_stop_time = None  # or do that?


        self._watering_coroutine = None
        self._should_launch_watering_coroutine = config["run_watering_coroutine"]

    async def _watering_execution_coroutine(self):
        """Is active as long as there are tasks."""
        self._gpio.set_state(self.gpio_pin, 1)
        while self._remaining_duration:


    def start_background_task(self):
        """ Should the actuator need to run an async background task, create and launch it here. """
        pass

    def start_watering(self, tasks: List[WateringTask]):

        self.logger.info(f"Received new watering tasks: {new_tasks}")
        for nt in new_tasks:
            if nt.zone == self.managed_zone:
                self._remaining_duration += nt.duration
        if not self._remaining_duration or self._watering_coroutine:
            return

        if self._should_launch_watering_coroutine:
            self._watering_coroutine = asyncio.create_task(
                self._watering_execution_coroutine())
        else:
            self._watering_coroutine = None

    def stop_watering(self, zones=[]):
        # TODO: How to identify zones?
        raise NotImplementedError()

    # === system state info ===

    def is_watering_active(self) -> bool:
        raise NotImplementedError()

    def are_tasks_left(self) -> bool:
        """ Returns whether watering is active or there are still scheduled tasks. """
        raise NotImplementedError()

    def get_remaining_time_current_zone(self) -> int:
        """ Returns the remaining watering duration for the current zone in seconds. """
        raise NotImplementedError()

    def get_remaining_time_all_zones(self) -> int:
        """ Returns the remaining watering duration for all zones in seconds. """
        raise NotImplementedError()

    def get_current_zone(self) -> str:
        # TODO: How to identify zones?
        raise NotImplementedError()
