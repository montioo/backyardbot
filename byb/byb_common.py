#
# byb_common.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from collections import namedtuple


# TODO: Not happy with either one

TOPIC_START_WATERING = "TOPIC_START_WATERING"
TopicStartWateringMessage = namedtuple(
    "TopicStartWateringMessage",
    "zones durations"  # [int] [int]
)

# class TopicStartWatering:
#     name = "TOPIC_START_WATERING"
#     message = namedtuple("message", "zones durations")