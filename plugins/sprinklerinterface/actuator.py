#
# actuator.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import time
import asyncio

from framework.utility import create_logger


@dataclass
class WateringTask:
    zone: str      # .zone = 0: water all zones
    duration: int  # .duration = 0: use cooldown duration

    def __repr__(self):
        return f"({self.zone}, {self.duration})"


class ActuatorInterface(ABC):
    """
    Interface for actuators. Implementations of this class take care of
    actually watering and thus controlling the gpio ports. It abstracts in a
    way that a calling function only has to give the tasks (a list of
    WateringTask instances ) and this class will then immediately start the
    watering. This class does NOT implement any scheduling functions in a way
    that you could give a channel and a time at which the watering should be
    executed - timing functions are implemented in the timecontrol plugin. An
    ActuatorInterface subclass will always take immediate action.
    """

    def __init__(self, managed_zones, name, config):
        logger_config = config.get("logging", {})
        self._should_launch_watering_coroutine = config.get("run_watering_coroutine", True)
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name, logger_config)
        # Callbacks for certain events?
        self.watering_stopped_function = lambda: None
        self.watering_started_function = lambda channel, duration: None
        self.reached_watering_time_limit = lambda channel, time_left: None

        self.name = name
        self.managed_zones = managed_zones

        # watering coroutine related
        self._watering_coroutine = None

        # sleeping and event handling
        self._evt = asyncio.Event()
        self._sleep_until = None

    def start_background_task(self):
        """ Should the actuator need to run an async background task, it will
        be created and launched here. """
        if self._should_launch_watering_coroutine:
            self._watering_coroutine = asyncio.create_task(
                self.watering_execution_coroutine())

    @abstractmethod
    async def watering_execution_coroutine(self):
        """ Will be launched shortly after the backyardbot is started. """
        # TODO: Introduce `should_shutdown` flag
        pass

    @abstractmethod
    def start_watering(self, new_tasks: List[WateringTask]):
        raise NotImplementedError()

    @abstractmethod
    def stop_watering(self, zones=[]):
        # TODO: How to identify zones?
        raise NotImplementedError()

    # === system state info ===

    @abstractmethod
    def is_watering_active(self) -> bool:
        raise NotImplementedError()

    def is_watering_cooldown_active(self) -> bool:
        # Most actuators don't need cooldowns
        return False

    @abstractmethod
    def are_tasks_left(self) -> bool:
        """ Returns whether watering is active or there are still scheduled tasks. """
        raise NotImplementedError()

    @abstractmethod
    def get_remaining_time_current_zone(self) -> int:
        """ Returns the remaining watering duration for the current zone in seconds. """
        raise NotImplementedError()

    @abstractmethod
    def get_remaining_time_all_zones(self) -> int:
        """ Returns the remaining watering duration for all zones in seconds. """
        raise NotImplementedError()

    @abstractmethod
    def get_current_zone(self) -> Optional[str]:
        # TODO: How to identify zones?
        raise NotImplementedError()

    def get_remaining_cooldown_time(self) -> int:
        """
        Returns the remaining cooldown duration. Only needs to be implemented
        if the actuator needs a cooldown. A cooldown allows the actuator to
        catch a break before watering the next zone.
        """
        # Most actuators don't need cooldowns
        return 0

    # TODO: Should reading the water level be implemented by the actuator or should a sensor be maintained by a sensor plugin?
    # @abstractmethod
    # def get_remaining_water(self) -> float:
    #     """
    #     For actuators that don't have running water supply, return percentage
    #     of remaining water in [0, 1]
    #     """
    #     return 1.0

    ### Background Task Sleeping ###
    ### ------------------------ ###

    async def sleep_until_timeout(self):
        """
        Will pause the execution of this coroutine while waiting for a
        timeout. Execution can be resumed if the waiting time elapsed or the
        waiting time was set to zero by another coroutine.
        """
        # wait for: ( event_triggered  or  time_up )
        while True:
            if self._sleep_until is None:
                return
            sleep_duration = max(0, self._sleep_until - time.time())
            try:
                # Wait until timeout runs out or event is triggered. Event
                # trigger can be used to update the sleep duration.
                await asyncio.wait_for(self._evt.wait(), sleep_duration)
            except asyncio.TimeoutError:
                pass

            if not self._evt.is_set():
                # Timeout ran out. Return
                self._sleep_until = None
                self.logger.debug("sleep_until_timeout - timeout ran out")
                return

            self.logger.debug("sleep_until_timeout - timeout duration updated")
            # Event triggered. This means the timeout duration was updated.
            # Clear event and continue.
            self._evt.clear()

    async def sleep_while_no_timout_set(self):
        while True:
            if self._sleep_until is not None:
                self.logger.debug("sleep_while_no_timout_set - timeout duration added")
                return
            try:
                # Wait until event is triggered. Event will be triggered by
                # another coroutine if it sets a timeout.
                await asyncio.wait_for(self._evt.wait(), None)
            except asyncio.TimeoutError:
                pass

            # Clear event and continue. Will then return if a timeout is set.
            self._evt.clear()

    def set_timeout(self, timeout_duration):
        """
        Sets a new timeout. A timeout is defined by the timestamp until which
        the coroutine should sleep. The sleep duration is updated in the
        watering coroutine as the event is set. The watering coroutine will
        update the sleeping duration and continue to sleep.
        """
        self.set_wakeup_time(time.time() + timeout_duration)

    def add_to_timeout(self, additional_sleep_duration):
        if not self._sleep_until:
            self.set_timeout(additional_sleep_duration)
            return
        self.set_wakeup_time(self._sleep_until + additional_sleep_duration)

    def set_wakeup_time(self, sleep_until):
        """
        Sets a new timeout. A timeout is defined by the timestamp until which
        the coroutine should sleep. The sleep duration is updated in the
        watering coroutine as the event is set. The watering coroutine will
        update the sleeping duration and continue to sleep.
        """
        self._sleep_until = sleep_until
        self._evt.set()
        # sleep timeout will trigger, notice that the timeout duration has been updated and continue to sleep.

    def reset_timout(self):
        """ Triggers the event and sets the timeout to zero, which will make
        the sleep or wait for event coroutine return. """
        self._sleep_until = None
        self._evt.set()

    def get_duration_until_wakeup_time(self):
        if not self._sleep_until:
            return None
        return self._sleep_until - time.time()
