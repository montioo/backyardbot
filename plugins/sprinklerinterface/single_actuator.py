#
# single_actuator.py
# backyardbot
#
# Created: December 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from plugins.sprinklerinterface.actuator import ActuatorInterface, WateringTask
from plugins.sprinklerinterface.gpio import DebugGpioInterface, RaspiGpioInterface
from typing import List, Optional


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

    def __init__(self, managed_zones, display_name, config):
        super().__init__(managed_zones, display_name, config)

        self.gpio_pin = config["gpio_pin"]

        if config.get("use_debug_gpio", False):
            self._gpio = DebugGpioInterface([self.gpio_pin], config)
        else:
            self._gpio = RaspiGpioInterface([self.gpio_pin], config)

    async def watering_execution_coroutine(self):
        """ Is active as long as there are tasks. """
        while True:
            self.logger.debug("Waiting for timout to be set")
            await self.sleep_while_no_timout_set()
            self.logger.debug("Timout was set")

            # Timeout was set -> activate watering
            self._gpio.set_state(self.gpio_pin, 1)
            self.logger.debug("Activated gpio. Waiting for timeout to end")
            await self.sleep_until_timeout()
            self.logger.debug("Timout ended")
            self._gpio.set_state(self.gpio_pin, 0)

    def start_watering(self, new_tasks: List[WateringTask]):
        """
        Adds the durations of the arrived tasks to the timeout for the
        watering coroutine. But only if the zone in the task matches the zone
        that this actuator manages.
        """
        self.logger.info(f"Received new watering tasks: {new_tasks}")
        for nt in new_tasks:
            if nt.zone == self.managed_zones[0]:
                self.add_to_timeout(nt.duration)

    def stop_watering(self, zones=[]):
        if self.managed_zones[0] in zones:
            # sets the timeout to zero, thus making
            self.reset_timout()

    # === system state info ===

    def is_watering_active(self) -> bool:
        return self._gpio.is_pin_active(self.gpio_pin)

    def are_tasks_left(self) -> bool:
        """ Returns whether watering is active or there are still scheduled tasks. """
        # Since this actuator only controls one physical actuator there is no task list.
        return self.is_watering_active()

    def get_remaining_time_current_zone(self) -> int:
        """ Returns the remaining watering duration for the current zone in seconds. """
        return self.get_duration_until_wakeup_time()

    def get_remaining_time_all_zones(self) -> int:
        """ Returns the remaining watering duration for all zones in seconds. """
        # This acutator only maintinas one zone.
        return self.get_remaining_time_current_zone()

    def get_current_zone(self) -> Optional[str]:
        return self.managed_zones[0] if self.is_watering_active() else None
