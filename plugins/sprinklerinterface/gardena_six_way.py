#
# gardena_six_way.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import time
import asyncio
from dataclasses import dataclass
from typing import Set

from plugins.sprinklerinterface.actuator import ActuatorInterface
from plugins.sprinklerinterface.gpio import DebugGpioInterface, RaspiGpioInterface
from framework.memory import Database


@dataclass
class ChannelTask:
    """
    Similar to actuator.WateringTask but it holds a channel number instead of
    a zone str. The six way sprinkler has six outputs and the order in which
    they are controlled is important. Thus the zones managed by this actuator
    are mapped to channels.
    """
    channel: int = 0    # .channel = 0: water all zones
    duration: int = 0   # .duration = 0: use cooldown duration

    def __repr__(self):
        return f"({self.channel}, {self.duration})"


class SixWayActuator(ActuatorInterface):
    """
    Watering Handler for Gardena 6 Way Water Distributor.
    It supports the cooldowns that are necessary for that thing.
    """

    def __init__(self, managed_zones, display_name, config):
        """
        Initialize sprinkler interface.
        :param config: Configuration dictionary
        :param runWateringThread: Determines whether a watering
            thread should be launched (debug and testing)
        """
        super().__init__(managed_zones, display_name, config)

        if config.get("use_debug_gpio", False):
            self._gpio = DebugGpioInterface([config["gpio_pin"]], config)
        else:
            self._gpio = RaspiGpioInterface([config["gpio_pin"]], config)

        self._channel_state_db = Database.get_db_for(config["channel_state_db"])

        self._active_channel = -1
        self._load_active_channel()
        self.logger.debug(f"Loaded active channel: {self._active_channel}")
        self._gpio_pin = config["gpio_pin"]
        self._channel_count = len(managed_zones)
        self._zone_channel_mapping = {z: i+1 for i, z in enumerate(managed_zones)}

        self._watering_tasks = []

        self._watering_stop_time = 0
        self._cooldown_duration = config["cooldown_duration"]

    # === Private methods ===
    # === --------------- ===

    async def watering_execution_coroutine(self):
        """
        Method that will run forever in a separate thread and take care
        of the actual watering. It will read tasks from the list that this
        class holds.
        """
        # TODO: Adapt to use advantages of new ActuatorInterface
        while True:

            if not self._watering_tasks or \
               self._watering_stop_time + self._cooldown_duration > time.time():
                await asyncio.sleep(1)
                continue

            self._watering_stop_time = time.time()
            self._gpio.set_state(self._gpio_pin, 1)
            self.logger.debug(f"Activated watering on channel {self._active_channel}, scheduled tasks: {self._watering_tasks}")

            while True:

                if self._watering_tasks and \
                   self._watering_tasks[0].channel == self._active_channel:

                    current_task = self._watering_tasks.pop(0)
                    self._watering_stop_time += current_task.duration
                    await self.state_updated_callback()
                    self.logger.info(f"Found new watering task for current channel: {current_task}")

                await asyncio.sleep(1)

                if time.time() > self._watering_stop_time:
                    self.logger.info("Done watering.")
                    break

            self._gpio.set_state(self._gpio_pin, 0)
            self._increase_watering_channel()
            await self.state_updated_callback()

    # === utility ===

    def _increase_watering_channel(self):
        self._active_channel += 1
        if self._active_channel > self._channel_count:
            self._active_channel = 1
        self._store_active_channel()
        self.logger.info(f"Active watering channel: {self._active_channel}")

    def _load_active_channel(self):
        db_contents = self._channel_state_db.all()
        if len(db_contents) != 1:
            self._channel_state_db.truncate()
            self._active_channel = 1
            self.logger.info("Couldn't find db entry with active channel.")
            # table is empty => insert active channel
            self._channel_state_db.insert({"active_channel": self._active_channel})
        else:
            self._active_channel = db_contents[0]["active_channel"]
            self.logger.info(f"Loaded last active channel from db: {self._active_channel}")

    def _store_active_channel(self):
        # table has active channel in it => overwrite
        self._channel_state_db.update({"active_channel": self._active_channel})

    # === Public methods ===
    # === -------------- ===

    def start_watering(self, new_tasks):
        """
        Will immediately start executing the given tasks.
        Can be called multiple times even if the watering is still in progress.
        Will add to the list of tasks.
        If current channel doesn't align, new tasks for switching will be introduced.
        Tasks with channel 0 (i.e. all channels) will be replaced by an individual
            task for each channel.
        :param new_tasks: list of WateringTask objects
        """
        self.logger.info(f"Received new watering tasks: {new_tasks}")
        # maps zones to channels
        channel_tasks = []
        for nt in new_tasks:
            if nt.zone in self._zone_channel_mapping.keys():
                channel = self._zone_channel_mapping[nt.zone]
                channel_tasks.append(ChannelTask(channel, nt.duration))
        if channel_tasks:
            self.update_watering_tasks(channel_tasks)

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

        tasks = [ChannelTask(c, tasks_dict[c]) for c in range(1, self._channel_count+1)]
        ordered_tasks = tasks[self._active_channel-1:] + tasks[:self._active_channel-1]

        # create list and sort it to
        final_tasks = []
        for task in reversed(ordered_tasks):
            if not final_tasks and task.duration == 0:
                continue
            allow_current_padding = task.channel != self._active_channel or not self.is_watering_active()
            if task.duration < self._cooldown_duration and allow_current_padding:
                final_tasks.append(ChannelTask(task.channel, self._cooldown_duration))
                continue
            final_tasks.append(task)
        self._watering_tasks = list(reversed(final_tasks))
        self.logger.debug(f"Updated watering tasks: {self._watering_tasks}")

    def stop_watering(self, zones: Set[str]):
        channels_to_stop = {self._zone_channel_mapping[z] for z in zones if z in self._zone_channel_mapping}
        if not channels_to_stop:
            # stop all zones if no zones are given
            self._watering_tasks = []
            self.logger.info("Stop watering for all zones")
        else:
            # remove zones in question from watering tasks
            self._watering_tasks = [wt for wt in self._watering_tasks if wt.channel not in channels_to_stop]
            self.logger.info(f"Stop watering for channels: {channels_to_stop}")
        if self._active_channel in channels_to_stop:
            # if channel is active, stop the watering for this zone.
            self._watering_stop_time = time.time()
        if self._watering_tasks:
            self.update_watering_tasks()

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
        duration = self.get_remaining_time_current_zone()
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
