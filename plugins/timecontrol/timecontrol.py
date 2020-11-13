#
# timecontrol.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
from framework.communication import Topics, BaseMessage, WebsocketRequest
from framework.memory import Database
from byb.byb_common import TOPIC_START_WATERING, StartWateringPayload, TIMETABLE_DB_NAME
from plugins.timecontrol.tc_task import Task
import time


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

        self.command_map = {
            "skip_next_watering": lambda _: self.skip_next_watering(),
            "toggle_auto_mode": self.toggle_auto_mode
        }

        self.timetable_db = Database.get_db_for(TIMETABLE_DB_NAME)
        self.register_topic_callback("database_update/" + TIMETABLE_DB_NAME, self._timetable_updated_callback)

        ws_backend_topic = f"websocket/{self.name}/backend"
        self.register_topic_callback(ws_backend_topic, self.ws_message_from_frontend)

        ws_new_client_topic = "websocket/new_client"
        self.register_topic_callback(ws_new_client_topic, self.new_ws_client)

        self._load_tasks()

    async def ws_message_from_frontend(self, msg):
        """
        Processes a message from frontend. Changes the state of the plugin
        and responds with an updated state description.
        """
        try:
            data = msg.payload
            command = data["command"]
            payload = data["payload"]
        except KeyError:
            self.logger.info(f"received invalid message from frontend: {msg}")
            return

        if command in self.command_map.keys():
            self.command_map[command](payload)

        await self.send_updated_state()

    async def new_ws_client(self, msg):
        """ Sends the current system state only to the new websocket client. """
        await self.send_updated_state(msg.ws_id)

    async def send_updated_state(self, ws_id=-1):
        """ Prepares a message that tells the frontend to update the UI with new data. """
        m = {
            "command": "plugin_state",
            "payload": self.get_system_state()
        }
        await self.send_to_clients(m, ws_id=ws_id)


    # === Task Scheduling ===

    async def _timetable_updated_callback(self, msg):
        """
        Loads the updated timetable from the database and sends the updated
        system state to all clients.
        """
        self._load_tasks()
        await self.send_updated_state()

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
            # TODO: Even if auto mode was disabled, the previous execution timestamps were still saved in the task object.
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
                self.logger.info(f"Sent new watering action: {p}")


    # === Plugin State ===
    # === ------------ ===

    # Mostly for how to get data for the UI.

    # === Status Control ===

    def skip_next_watering(self):
        self.logger.info("Will skip next watering")
        if not self._auto_mode_enabled or not self._tasks:
            return
        self.logger.info("Will skip next watering - for real")
        group = self._get_next_group()
        self._reschedule_tasks(to_update=group)

    def start_auto_mode(self):
        self._reschedule_tasks(to_update=self._tasks)
        if self._tasks:
            self._auto_mode_enabled = True

    def stop_auto_mode(self):
        self._auto_mode_enabled = False

    def toggle_auto_mode(self, new_state):
        if new_state:
            self.start_auto_mode()
        else:
            self.stop_auto_mode()

    # === Status Info ===

    def get_next_task_time_day(self) -> str:
        """ Returns a string with time and day at which the next watering will occur. """
        # format 19:05 Uhr, Montags
        if not self._tasks:
            return " "
        # TODO: Return properties of the whole group?
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

    def get_system_state(self):
        auto_state = self.is_auto_mode_enabled()
        state_dict = {
            "auto_state": auto_state,
            # TODO: Use localization dict. Make localization dict available as self.localization
            # TODO: Don't use localization dict? Rather Let the frontend do that by transferring weekdays ids and such
            "next_time_day": self.get_next_task_time_day() if auto_state else "Auto mode disabled",
            "next_zone_duration": f"Zones: {self.get_next_task_zone()}, Duration: {self.get_next_task_duration()}"
        }
        return state_dict

