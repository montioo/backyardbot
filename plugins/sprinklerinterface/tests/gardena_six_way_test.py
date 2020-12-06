#
# gardena_six_way_test.py
# backyardbot
#
# Created: June 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import unittest
import os
from plugins.sprinklerinterface.gardena_six_way import ChannelTask, SixWayActuator
from plugins.sprinklerinterface.actuator import WateringTask
from framework.memory import Database

"""
Tests the sprinkler interface to make sure that watering tasks are scheduled
correctly. Input to the six way actuator are WateringTask objects which hold
a zone. Those are then mapped to the channels that the actuator maintains and
the output are thus ChannelTask objects.
"""

dummy_database_file = "/Users/monti/Documents/ProjectsGit/byb-github/dummy_db.json"


class TestSixWayActuator(unittest.TestCase):

    def setUp(self):

        global dummy_database_file
        Database.set_db_path(dummy_database_file)

        managed_zones = ["Z1", "Z2", "Z3", "Z4"]
        actuator_config = {
            "cooldown_duration": 7,
            "use_debug_gpio": True,
            "gpio_pin": 13,
            "run_watering_coroutine": False,
            "channel_state_db": "sprinkler_interface_actuator1_db",
        }

        self._channel_state_db = Database.get_db_for(actuator_config["channel_state_db"])
        self._channel_state_db.truncate()
        self._channel_state_db.insert({"active_channel": 3})

        # TODO: Why is name None? I mean not only here but also when instantiated by the plugin.
        self.actuator = SixWayActuator(managed_zones, None, actuator_config)

    def tearDown(self):
        Database.db.close()
        os.remove(dummy_database_file)

    def test_watering_list1(self):
        """ General tests for reading watering tasks in. """
        WT, CT = WateringTask, ChannelTask

        task_input_1 = [WT("Z4", 25), WT("Z4", 40), WT("Z1", 15), WT("Z3", 3)] \
            + [WT("Z1", 20), WT("Z2", 20), WT("Z3", 20), WT("Z4", 20)]  # replacing WT(0, 20),
        task_correct_1 = [CT(3, 20), CT(4, 85), CT(1, 35), CT(2, 20)]

        self.actuator.start_watering(task_input_1)
        self.assertEqual(self.actuator._watering_tasks, task_correct_1)

        task_input_2 = [WT("Z4", 45), WT("Z4", -20), WT("Z1", 15), WT("Z3", 15)]
        task_correct_2 = [CT(3, 35), CT(4, 130), CT(1, 50), CT(2, 20)]

        self.actuator.start_watering(task_input_2)
        self.assertEqual(self.actuator._watering_tasks, task_correct_2)

        task_input_3 = [WT("Z1", 20), WT("Z2", 20), WT("Z3", 20), WT("Z4", 20)]  # replacing WT(0, 20),
        task_correct_3 = [CT(3, 55), CT(4, 150), CT(1, 70), CT(2, 40)]

        self.actuator.start_watering(task_input_3)
        self.assertEqual(self.actuator._watering_tasks, task_correct_3)

    def test_watering_list2(self):
        """ Tests padding with short activations and replacing those later. """
        WT, CT = WateringTask, ChannelTask

        task_input_1 = [WT("Z2", 20)]
        task_correct_1 = [CT(3, 7), CT(4, 7), CT(1, 7), CT(2, 20)]

        self.actuator.start_watering(task_input_1)
        self.assertEqual(self.actuator._watering_tasks, task_correct_1)

        task_input_2 = [WT("Z4", 15)]
        task_correct_2 = [CT(3, 7), CT(4, 15), CT(1, 7), CT(2, 20)]

        self.actuator.start_watering(task_input_2)
        self.assertEqual(self.actuator._watering_tasks, task_correct_2)

    def test_watering_list3(self):
        """ Tests stopping all zones. """
        WT, CT = WateringTask, ChannelTask

        task_input_1 = [WT("Z3", 20), WT("Z4", 20)]
        task_correct_1 = [CT(3, 20), CT(4, 20)]

        self.actuator.start_watering(task_input_1)
        self.assertEqual(self.actuator._watering_tasks, task_correct_1)

        self.actuator.stop_watering()

        task_correct_2 = []
        self.assertEqual(self.actuator._watering_tasks, task_correct_2)

    def test_watering_list4(self):
        """ Tests stopping individual zones. """
        WT, CT = WateringTask, ChannelTask

        task_input_1 = [WT("Z3", 20), WT("Z4", 20), WT("invalid_zone", 30)]
        task_correct_1 = [CT(3, 20), CT(4, 20)]

        self.actuator.start_watering(task_input_1)
        self.assertEqual(self.actuator._watering_tasks, task_correct_1)

        self.actuator.stop_watering(zones=[1, 4])

        task_correct_2 = [CT(3, 20)]
        self.assertEqual(self.actuator._watering_tasks, task_correct_2)


if __name__ == '__main__':
    unittest.main()
