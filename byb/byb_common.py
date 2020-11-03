#
# byb_common.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from collections import namedtuple
from dataclasses import dataclass
from typing import List


# == Database Names ==

TIMETABLE_DB = "time_schedule_table"


# == Topic Definitions ==

TOPIC_START_WATERING = "TOPIC_START_WATERING"

@dataclass
class StartWateringMessage:
    zones: List[int]
    durations: List[int]

    def __repr__(self):
        return "({}, {})".format(self.zones, self.durations)

# which one of those?

@dataclass
class WateringTask:
    zone: int = 0       # .zone = 0: water all channels  NO
    duration: int = 0   # .duration = 0: use cooldown duration

    def __repr__(self):
        return "({}, {})".format(self.zone, self.duration)