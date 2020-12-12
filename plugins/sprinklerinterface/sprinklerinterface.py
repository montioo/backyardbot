#
# sprinklerinterface.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
from framework.memory import Database
from framework.communication import Topics, BaseMessage
from byb.byb_common import TOPIC_START_WATERING, ZONE_DB_NAME, TOPIC_ZONES_UPDATED, ZonesUpdatedPayload

from plugins.sprinklerinterface.actuator import WateringTask
from plugins.sprinklerinterface.single_actuator import SingleActuator
from plugins.sprinklerinterface.gardena_six_way import SixWayActuator

from typing import List


# TODO: Parse files in plugin folder for actuator subclasses
actuator_implementations = {
    "SixWayActuator": SixWayActuator,
    "SingleActuator": SingleActuator
}


class WateringPlugin(Plugin):
    """
    Tasks of this Plugin:
    - Take lists of zones and durations and call actuators
    - asyncio events to start/stop watering and no loops with sleep(1)
    """

    def initialize(self, settings):
        self._command_handlers = {
            "start_watering": self.start_watering_callback_ws,
            "stop_watering": self.stop_watering_callback_ws
        }

        # IDEA: Expand websocket communication so that frontend js can send to any topic?
        self.zone_db = Database.get_db_for(ZONE_DB_NAME)

        ws_backend_topic = f"websocket/{self.name}/backend"
        self.register_topic_callback(ws_backend_topic, self.ws_message_from_frontend)

        ws_new_client_topic = "websocket/new_client"
        self.register_topic_callback(ws_new_client_topic, self.new_ws_client)

        self.register_topic_callback(TOPIC_START_WATERING, self.start_watering_callback_topic)
        self.actuators = []
        zones = self._initialize_actuators()
        self._update_zone_db(zones)

    async def event_loop(self):
        for actuator in self.actuators:
            actuator.start_background_task()

        await self.spin()

    # === WebSocket Interaction ===

    async def ws_message_from_frontend(self, msg):
        data = msg.payload
        self.logger.info(f"received a message from frontend: {data}")

        cmd = data.get("command", None)
        if cmd in self._command_handlers.keys():
            await self._command_handlers[cmd](data.get("payload", None))

    async def start_watering_callback_ws(self, data):
        """
        Read a message that was received via websocket and start the watering
        if the message contains valid data.
        """
        try:
            mm, ss = map(int, data["duration"].split(":"))
            duration = 60*mm + ss
            zone = data["zone"]
        except:
            self.logger.info(f"Received invalid payload for start_watering cmd from frontend: {data}")
            return

        task = WateringTask(zone, duration)
        self.logger.info(f"Starting watering task from frontend: {task}")
        await self.start_watering([task])

    async def stop_watering_callback_ws(self, data):
        if not isinstance(data, list):
            return
        zones_to_stop = set(data if data else self.zones)
        for actuator in self.actuators:
            # only hand zones to the actuator that it manages
            actuator.stop_watering(set(actuator.managed_zones) & zones_to_stop)

    async def new_ws_client(self, msg):
        """ Sends the current system state only to the new websocket client. """
        await self.send_state_update_to_clients(msg.ws_id)

    async def send_state_update_to_clients(self, ws_id=-1):
        actuator_states = self.get_actuator_states()
        msg = {
            "command": "update_frontend_state",
            "payload": actuator_states
        }
        # self.logger.info("compiled state:", actuator_states)
        await self.send_to_clients(msg, ws_id)

    # === Topic Callbacks ===

    async def start_watering_callback_topic(self, msg):
        """ Receives watering tasks from a topic and starts them. """
        data = msg.payload
        zones, durations = data.zones, data.durations
        tasks = map(lambda t: WateringTask(t[0], t[1]), zip(zones, durations))
        await self.start_watering(tasks)

    # === Actuator Interaction ===

    async def start_watering(self, tasks: List[WateringTask]):
        """ Immediately hands the watering tasks to the responsible actuators. """
        # dict that maps from multiple zones to the same list for an actuator
        task_mapping = {}
        for actuator in self.actuators:
            new_task_list = []
            for zone in actuator.managed_zones:
                task_mapping[zone] = new_task_list

        # append task to the list of tasks of the responsible actuator
        for task in tasks:
            if task.zone in task_mapping.keys():
                task_mapping[task.zone].append(task)
            else:
                self.logger.warn(f"Received task for unknown zone: {task}")

        # hand collected task lists to actuators
        for actuator in self.actuators:
            new_task_list = task_mapping[actuator.managed_zones[0]]
            actuator.start_watering(new_task_list)

        # Frontends are informed about updated watering state as soon as
        # actuators start doing the actual watering.

    # === Actuator and Zone Setup ===

    def _initialize_actuators(self):
        all_zones = []

        for actuator_config in self.settings["plugin_settings"]["actuators"]:
            actuator_class_name = actuator_config.get("python_class", None)
            if actuator_class_name not in actuator_implementations:
                self.logger.warning(f"{actuator_class_name} is not in the list of known implementations")
                continue

            managed_zones = actuator_config.get("zones", [])
            if not managed_zones:
                self.logger.warn(f"Managed zones for {actuator_class_name} instance are empty!")
                continue

            all_zones += managed_zones
            display_name = actuator_config.get("display_name", actuator_class_name)
            actuator_specific_settings = actuator_config.get("actuator_specific_settings", {})
            actuator = actuator_implementations[actuator_class_name](managed_zones, display_name, actuator_specific_settings)
            actuator.state_updated_callback = self.actuator_state_updated
            self.actuators.append(actuator)

        return all_zones

    def _update_zone_db(self, new_zones):
        """ Sets the list of zones and only updates the database if changes occurred. """
        old_zones_set = {zone["name"] for zone in self.zone_db.all()}
        new_zones_set = set(new_zones)
        if old_zones_set != new_zones_set:
            self.logger.info("Going to update zone DB")
            self.logger.info(f"  Old: {old_zones_set}")
            self.logger.info(f"  New: {new_zones_set}")
            zone_dicts = [{"name": zone_name} for zone_name in new_zones]
            self.zone_db.truncate()
            self.zone_db.insert_multiple(zone_dicts)

            p = ZonesUpdatedPayload(sorted(new_zones))
            m = BaseMessage(TOPIC_ZONES_UPDATED, p)
            Topics.send_message(m)

        self.zones = sorted(new_zones)

    # === Frontend Data ===

    def get_actuator_states(self):
        actuator_states = []

        for actuator in self.actuators:

            # building descriptive string
            desc = f"{actuator.display_name}: "
            remaining_time = None

            if actuator.is_watering_active():
                desc += f"Watering Zone {actuator.get_current_zone()}, remaining time:"
                remaining_time = actuator.get_remaining_time_current_zone()
            elif actuator.is_watering_cooldown_active():
                desc += "Cooldown active:"
                remaining_time = actuator.get_remaining_cooldown_time()
            else:
                # watering is off:
                desc += self.localization["actuator_state_off_label"]

            # dict for a state per actuator:
            state_dict = {"description": desc, "remaining_time": remaining_time}
            actuator_states.append(state_dict)

        return actuator_states

    def calc_render_data(self):
        return {
            "zones": self.zones
        }

    # === Actuator State Callback ===

    async def actuator_state_updated(self):
        # Launch new coroutine here to not block execution? No, because the
        # actuator will wait for the next time after the watering state
        # changed.
        await self.send_state_update_to_clients()
