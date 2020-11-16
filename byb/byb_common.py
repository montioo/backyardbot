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

TIMETABLE_DB_NAME = "time_schedule_table"
ZONE_DB_NAME = "zone_info_table"


# == Topic Definitions ==

TOPIC_START_WATERING = "TOPIC_START_WATERING"

@dataclass
class StartWateringPayload:
    # TODO: Move all zone descriptors from int to str
    zones: List[int]        # .zone = 0: water all channels  NO
    durations: List[int]    # .duration = 0: use cooldown duration

    def __repr__(self):
        return f"StartWateringPayload: [(zone, duration), ..]: {list(zip(self.zones, self.durations))}"


TOPIC_ZONES_UPDATED = "TOPIC_ZONES_UPDATED"

@dataclass
class ZonesUpdatedPayload:
    zones: List[str]