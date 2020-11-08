#
# timecontrol.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
from framework.communication import Topics, BaseMessage
from framework.memory import Database
from byb.byb_common import TOPIC_START_WATERING, StartWateringPayload, TIMETABLE_DB_NAME
from tc_task import Task

import asyncio
import time
import datetime
# from sprinklerinterface import WateringTask, SprinklerInterface
# import threading
from typing import List, Tuple
# import utility
import uuid


class TimeControlPlugin(Plugin):
    """
    Reads the database and calculates next watering times. If the automatic
    mode is enabled, start watering signals will be sent based on database
    entries.
    """

    def initialize(self, settings):

        # Holds all defined tasks. It is assumed to be sorted by next execution timestamp
        #  Tasks are sorted using the timestamp at which they will be executed next
        #  which uses the magic method __gt__. Tasks are checked for equality (__eq__) by
        #  comparing their ids, NOT their timestamps.
        self._tasks = []
        self._auto_mode_enabled = True

        self.timetable_db = Database.get_db_for(TIMETABLE_DB_NAME)
        self.register_topic_callback("database_update/" + TIMETABLE_DB_NAME, self._timetable_updated_callback)

        self._load_tasks()


    # === Private methods ===
    # === --------------- ===

    async def _timetable_updated_callback(self, msg):
        # Ignore msg and load updated timetable
        self._load_tasks()

    def _load_tasks(self):
        """
        Loads entries from timetable DB, creates Task objects from them (i.e.
        objects that know the soonest possible execution time) and sorts
        them, so that the next task is first in the list.
        """
        entries = Database.as_dict_with_id(self.timetable_db.all(), id_tag="ID")
        self._tasks = sorted([Task(entry) for entry in entries])

        self.logger.info("Fetched tasks from DB:")
        for task in self._tasks:
            self.logger.info(f"{task}")

    def _reschedule_tasks(self, to_update):
        """
        Updates the next execution times for the tasks that are given and
        makes sure that the list of tasks is still sorted by next execution
        time.
        """
        for task in to_update:
            task.update_next_execution_timestamp()
        self._tasks.sort()

    def _get_next_group(self):
        """
        A group represents a list of watering tasks which are scheduled for
        execution at the same time. Channels may appear multiple times but
        sorting or merging isn't necessary as this is handled by the
        sprinkler interface.
        """
        task_group = []
        for task in self._tasks:
            if task.next_execution_timestamp != self._tasks[0].next_execution_timestamp:
                break
            task_group.append(task)
        return task_group

    async def event_loop(self):
        """
        Coroutine that runs forever and hands new watering tasks to the
        sprinkler interface when it's time.
        """
        # TODO: Don't run every second but wait for the next task. But: How to change the waiting time as the table gets updated?
        rate = 1
        while await self.spin_once(rate):

            if not self._tasks or not self._auto_mode_enabled:
                continue

            next_task_ts = self._tasks[0].next_execution_timestamp
            if time.time() >= next_task_ts and next_task_ts != 0:
                group = self._get_next_group()
                self._reschedule_tasks(to_update=group)

                actions = [action for task in group for action in task.actions()]
                zones = [action.zone for action in actions]
                durations = [action.duration for action in actions]
                p = StartWateringPayload(zones, durations)
                m = BaseMessage(TOPIC_START_WATERING, payload=p)
                Topics.send_message(m)
                self.logger.info("Sent new watering action: {}".format(p))


    # === Plugin State ===
    # === ------------ ===

    # Mostly for how to get data for the UI.

    # === Status Control ===

    def skip_next_watering(self):
        if not self._auto_mode_enabled or not self._tasks:
            return
        group = self._get_next_group()
        self._reschedule_tasks(to_update=group)

    def start_auto_mode(self):
        self._reschedule_tasks(to_update=self._tasks)
        if self._tasks:
            self._auto_mode_enabled = True

    def stop_auto_mode(self):
        self._earliest_watering_timestamp = 0
        self._auto_mode_enabled = False

    # === Status Info ===

    def get_next_task_time_day(self) -> str:
        """ Returns a string with time and day at which the next watering will occur. """
        # format 19:05 Uhr, Montags
        if not self._tasks:
            return " "
        return str(self._tasks[0])

    def get_next_task_zone(self) -> str:
        """ Returns a string with next zones to be watered. """
        if not self._tasks:
            return " "
        return str(self._tasks[0].zones)[1:-1]

    def get_next_task_duration(self):
        if not self._tasks:
            return " "
        return str(self._tasks[0].dynamic_duration())

    def is_auto_mode_enabled(self):
        return self._auto_mode_enabled


