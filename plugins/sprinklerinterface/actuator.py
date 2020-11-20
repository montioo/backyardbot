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
import logging
from typing import List

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

    def __init__(self, managed_zones, name, logger_config):
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name, logger_config)
        # Callbacks for certain events?
        # self.watering_stopped_function = lambda:None
        # self.watering_started_function = lambda channel, duration:None
        # self.reached_watering_time_limit = lambda channel, time_left:None
        self.name = name
        self.managed_zones = managed_zones

    @abstractmethod
    def start_watering(self, tasks: List[WateringTask]):
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
    def get_current_zone(self) -> int:
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
