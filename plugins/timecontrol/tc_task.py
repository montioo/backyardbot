#
# tc_task.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import asyncio
import time
import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

# TODO: This one needs refactoring to not consist of three classes for one simple job.

class ScheduledTime(object):

    def __init__(self, time_hh, time_mm, weekday):
        # if args and type(args[0]) is str:
        #     raise NotImplementedError("ScheduledTime from string is not expected")
        #     # parameters = args[0].split(";")
        #     # self.hour , self.minute = int(parameters[0][:2]), int(parameters[0][3:])
        #     # self.weekday, self.channel, self.duration = map(int, parameters[1:4])

        # can be used by keyword args or to construct from dict.
        self.hour = time_hh
        self.minute = time_mm
        # If weekday == 7, watering should happen every day.
        self.weekdays = set(range(7)) if weekday == 7 else {weekday}

        self.next_execution_timestamp = 0

    # === Public methods ===
    # === -------------- ===

    def next_occurrence(self, earliest_time=time.time()):
        now = datetime.datetime.now()
        # TODO: If minutes are equal because this task was just activated, the just activated
        #   task will be listed as the next scheduled task.
        next_execution_datetime = datetime.datetime(now.year, now.month, now.day, self.hour, self.minute)

        while True:
            self.next_execution_timestamp = time.mktime(next_execution_datetime.timetuple())
            if self.next_execution_timestamp > earliest_time and \
                next_execution_datetime.weekday() in self.weekdays:
                break
            next_execution_datetime += datetime.timedelta(days=1)
        return self.next_execution_timestamp

    def asdict(self):
        print("!"*15, "querying time as dict not correct atm.")
        return {"hour": self.hour, "minute": self.minute, "weekdays": sorted(self.weekdays)}

    # === Magic methods ===
    # === ------------- ===

    def __eq__(self, other):
        return self.minute == other.minute and self.hour == other.hour \
            and self.weekdays == other.weekdays  # comparing sets, order doesn't matter

    def __repr__(self):
        # TODO: Use localization data
        weekdays_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun", "daily"]
        weekdays = "daily" if len(self.weekdays) == 7 else [weekdays_names[w] for w in sorted(self.weekdays)]
        # print("!"*15, "querying time as str not correct atm.")
        return "time: {:02}:{:02}, days: {}".format(self.hour, self.minute, weekdays)

    # === Private methods ===
    # === --------------- ===

    def _get_time_str_hh_mm(self):
        return "{:02}:{:02}".format(self.hour, self.minute)

    # === Computed properties ===
    # === ------------------- ===

    time_str_hh_mm = property(_get_time_str_hh_mm)


if __name__ == "__main__":
    # TODO: Do proper testing instead of this.
    st = ScheduledTime(16, 45, 6)
    st.next_occurrence()


@dataclass
class Action:
    zone: int = 0    # .channel = 0: water all channels
    duration: int = 0   # .duration = 0: use cooldown duration

    def __repr__(self):
        return f"({self.zone}, {self.duration})"


class Task:
    """
    Holds a task. When the time has come, it will calculate the appropriate duration by evaluating the
    modifiers and forward the durations for each zone to the responsible actuators (somehow)
    """

    # def __init__(self, specification=None, sensor_handle=None):
    def __init__(self, db_timetable_entry):

        # Timetable database structure
        # {
        #     "time_hh": int,
        #     "time_mm": int,
        #     "weekday": int,
        #     "zones": [int],
        #     "duration": int
        # }

        self.id = db_timetable_entry["ID"]
        self.zones = db_timetable_entry["zones"]
        time_hh, time_mm, weekday = map(lambda tag: db_timetable_entry[tag], ["time_hh", "time_mm", "weekday"])
        self.planned_time = ScheduledTime(time_hh, time_mm, weekday)
        self.duration = db_timetable_entry["duration"]
        # self.modifier = []
        self.next_execution_timestamp = self.planned_time.next_occurrence()

    def update_next_execution_timestamp(self):
        """ Finds the next execution timestamp after the current one. """
        self.next_execution_timestamp = self.planned_time.next_occurrence(self.next_execution_timestamp)

    def skip_next_execution(self):
        raise NotImplementedError("not even the NotImplementedError is implemented")

    def dynamic_duration(self):
        """ Returns the duration that is affected by the modifier evaluation. """
        # TODO: Evaluate modifiers with sensor readings
        return self.duration

    def actions(self):
        """
        Returns a list of actions, each holding a zone and the duration
        for which the action should last.
        """
        dyn_duration = self.dynamic_duration()
        return [Action(z, dyn_duration) for z in self.zones]

    def __gt__(self, other):
        """ Sorting is done with `__gt__` with respect to planned execution times. """
        return self.next_execution_timestamp > other.next_execution_timestamp

    def __eq__(self, other):
        """ Comparisons to identify entries are done with `__eq__` with respect ot ids. """
        # TODO: Is this still needed?
        return self.id == other.id

    def __str__(self):
        # implement representation based on next execution weekday and time
        # TODO: This causes wrong (to much) info in the UI. Remove zones or whatever.
        return f"task id: {self.id}, {self.planned_time}, zones: {self.zones}"

    # === Deprecated ===

    # @classmethod
    # def decode(cls, dct):
    #     # TODO: Update:
    #     try:
    #         t = Task()
    #         t._zones = dct["zones"]
    #         t._duration = dct["duration"]
    #         t._modifier = dct["modifier"]
    #         return t
    #     except KeyError:
    #         type_name = dct.__class__.__name__
    #         raise TypeError(f"{type_name} is not decodable into Task object")

    # @classmethod
    # def encode(cls):
    #     # put all of the class' content into a dict with lists and stuff
    #     pass