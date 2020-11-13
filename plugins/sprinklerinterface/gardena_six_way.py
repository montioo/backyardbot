#
# gardena_six_way.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from abc import ABC, abstractmethod

import time
import asyncio
import logging
import datetime
from enum import Enum
from typing import Tuple, List
from collections import namedtuple
from dataclasses import dataclass

from plugins.sprinklerinterface.actuator import ActuatorInterface
from plugins.sprinklerinterface.gpio import GpioInterface, DebugGpioInterface, RaspiGpioInterface
from plugins.sprinklerinterface.sprinklerinterface import WateringTask


class SixWaySprinkler(ActuatorInterface):
    """
    Watering Handler for Gardena Wasserverteiler 6 Way.
    It supports the cooldowns that are necessary for that thing.
    """

    def __init__(self, managed_zones, name, config):
        logger_config = config["logging"]
        super(SixWaySprinkler, self).__init__(managed_zones, name, logger_config)
        """
        Initialize sprinkler interface.
        :param config: Configuration dictionary
        :param runWateringThread: Determines whether a watering
            thread should be launched (debug and testing)
        """

        if config["use_dummy_gpio"]:
            self._gpio = DebugGpioInterface(config, [config["gpio_pin"]])
        else:
            self._gpio = RaspiGpioInterface(config, [config["gpio_pin"]])

        self._channel_state_file = config["channel_state_file"]
        self._active_channel = -1
        self._load_active_channel()
        self._gpio_pin = config["gpio_pin"]
        self._channel_count = config["channel_count"]
        self.watering_cooldown_function = lambda cooldown_duration:None

        self._watering_tasks = []

        self._watering_stop_time = 0
        self._cooldown_duration = config["cooldown_duration"]

        if config["run_watering_coroutine"]:
            self._watering_coroutine = asyncio.create_task(self._watering_execution_coroutine())
        else:
            self._watering_coroutine = None

    # === Private methods ===
    # === --------------- ===

    async def _watering_execution_coroutine(self):
        """
        Method that will run forever in a separate thread and take care
        of the actual watering. It will read tasks from the list that this
        class holds.
        """

        while True:

            if not self._watering_tasks or \
                self._watering_stop_time + self._cooldown_duration > time.time():
                await asyncio.sleep(1)
                continue

            self._watering_stop_time = time.time()
            self._gpio.set_state(self._gpio_pin, 1)

            while True:

                if self._watering_tasks and \
                    self._watering_tasks[0].channel == self._active_channel:

                    current_task = self._watering_tasks.pop(0)
                    self._watering_stop_time += current_task.duration
                    self.watering_started_function(current_task.channel, self.get_remaining_time_current_channel())
                    self.logger.info(f"Found new watering task for current channel: {current_task}")

                await asyncio.sleep(1)

                if time.time() > self._watering_stop_time:
                    self.logger.info("Done watering.")
                    break

            self._gpio.set_state(self._gpio_pin, 0)
            self._increase_watering_channel()
            if self._watering_tasks:
                self.watering_cooldown_function(self._cooldown_duration)
            else:
                self.watering_stopped_function()

    # === utility ===

    def _increase_watering_channel(self):
        self._active_channel += 1
        if self._active_channel > self._channel_count:
            self._active_channel = 1
        self._store_active_channel()
        self.logger.info(f"Active watering channel: {self._active_channel}")

    def _load_active_channel(self):
        # TODO: Do this with framework.memory.Database
        try:
            with open(self._channel_state_file) as f:
                self._active_channel = int(f.readline())
                self.logger.info(f"Loaded last active channel from file: {self._active_channel}")
        except FileNotFoundError:
            self._active_channel = 1
            self.logger.info("Couldn't find file with active channel.")
            self._store_active_channel()

    def _store_active_channel(self):
        with open(self._channel_state_file , "w") as f:
            f.write(str(self._active_channel))

    # === Public methods ===
    # === -------------- ===

    def start_watering(self, new_tasks):
        """
        Will immediatly start executing the given tasks.
        Can be called multiple times even if the watering is still in progress.
        Will add to the list of tasks.
        If current channel doesn't align, new tasks for switching will be introduced.
        Tasks with channel 0 (i.e. all channels) will be replaced by an individual
            task for each channel.
        :param new_tasks: list of WateringTask objects
        """
        self.logger.info(f"Received new watering tasks: {new_tasks}")
        self.update_watering_tasks(new_tasks)

    def update_watering_tasks(self, new_tasks=[]):
        # create dict with durations from new and planned tasks. (no need to look at
        #   current task, because this was 'transfered' to self.watering_stop_time)
        tasks_dict = {i: 0 for i in range(1, self._channel_count+1)}
        for task in new_tasks + self._watering_tasks:
            if task.channel < 0 or task.channel > self._channel_count or task.duration <= 0:
                continue
            if task.channel != 0:
                # if task.channel == self._active_channel or task.duration > self._cooldown_duration:
                if task.duration > self._cooldown_duration:
                    tasks_dict[task.channel] += task.duration
            else:
                for i in range(1, self._channel_count+1):
                    tasks_dict[i] += task.duration

        tasks = [WateringTask(c, tasks_dict[c]) for c in range(1, self._channel_count+1)]
        ordered_tasks = tasks[self._active_channel-1:] + tasks[:self._active_channel-1]

        # create list and sort it to
        final_tasks = []
        for task in reversed(ordered_tasks):
            if not final_tasks and task.duration == 0:
                continue
            allow_current_padding = task.channel != self._active_channel or not self.is_watering_active()
            if task.duration < self._cooldown_duration and allow_current_padding:
                final_tasks.append(WateringTask(task.channel, self._cooldown_duration))
                continue
            final_tasks.append(task)
        self._watering_tasks = list(reversed(final_tasks))
        self.logger.debug(f"Updated watering tasks: {self._watering_tasks}")

    def stop_watering(self, zones=[]):
        if not zones:
            # stop all zones if no zones are given
            self._watering_tasks = []
            self.logger.info("Stop watering for all zones")
        else:
            # remove zones in question from watering tasks
            self._watering_tasks = [wt for wt in self._watering_tasks if wt.channel not in zones]
            self.logger.info(f"Stop watering for zones: {zones}")
        if self._active_channel in zones:
            # if zone is active, stop the watering for this zone.
            self._watering_stop_time = time.time()
        if self._watering_tasks:
            self.update_watering_tasks()
        # Use old implementation if selective stopping doesn't work.

    # === system state info ===

    def is_watering_active(self):
        return self._gpio.is_pin_active(self._gpio_pin)

    def is_watering_cooldown_active(self):
        # Don't display the cooldown for the last watering.
        return self.get_remaining_cooldown_time() != 0 and self._watering_tasks

    def are_tasks_left(self):
        return self.is_watering_active() or self._watering_tasks

    def get_remaining_time_current_zone(self):
        return max(0, int(self._watering_stop_time - time.time()))

    def get_remaining_time_all_zones(self):
        if not self._watering_tasks:
            return 0
        duration = self.get_remaining_time_current_channel()
        for task in self._watering_tasks:
            duration += task.duration
        duration += self._cooldown_duration * len(self._watering_tasks)
        return duration

    def get_current_zone(self):
        return self._active_channel

    def get_remaining_cooldown_time(self):
        t = time.time()
        lower_bound = self._watering_stop_time
        upper_bound = self._watering_stop_time + self._cooldown_duration
        if lower_bound < t < upper_bound:
            return upper_bound - t
        return 0