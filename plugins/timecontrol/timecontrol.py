#
# timecontrol.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import os
from framework.plugin import Plugin
from framework.communication import Topics
from byb.byb_common import TOPIC_START_WATERING, TopicStartWateringMessage


class TimeControlPlugin(Plugin):
    """
    Read the database and calculate next watering times.

    1. Read timetable database
    2. Determine next watering event -> display next event in frontend
    3. Once the time has come, send a message over a topic to trigger the watering
    """

    def initialize(self, settings):
        pass

    async def event_loop(self):
        # wait for next watering event
        zones, durations = [], []
        msg = TopicStartWateringMessage(zones, durations)
        Topics.send_message(TOPIC_START_WATERING, msg)
