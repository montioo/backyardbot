#
# main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import os
import json
import sys
import glob
import asyncio
from aiohttp import web
from .renderer import Renderer
from .utility import create_logger
from .communication import Topics, WebsocketRequest
from .event import EventComponent


def load_allowed_files(settings: dict):
    allowed_files = []
    # allowed_files |= set(glob.glob(settings.get("application", {}).get(file_list, [])))
    files = settings.get("application", {}).get("static_web_files", [])
    for f in files:
        if f not in allowed_files:
            allowed_files.append(f)

    return allowed_files

def get_html_template_file(settings: dict):
    return settings.get("application", {}).get("template_index", "web/index.html")


class Server(EventComponent):

    def __init__(self, settings_file, plugin_manager):
        settings = json.load(open(settings_file))
        super().__init__(settings)
        # TODO: Store global settings somewhere else?
        self.settings = settings

        self.ws_clients = set()

        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name)
        self.allowed_files = load_allowed_files(self.settings)

        # TODO: Have another object deal with this. Don't merge plugin maintenance and server stuff.
        self.plugins_list = plugin_manager.get_plugin_list()

        for plugin in self.plugins_list:
            plugin.register_server(self)
            self.allowed_files += plugin.css_files() + plugin.js_files()

            topic = "websocket/{}/frontend".format(plugin.name)
            self.register_topic_callback(topic, self.send_topic_over_ws)

        html_template_file = get_html_template_file(self.settings)
        self.renderer = Renderer(plugin_manager, html_template_file, self.allowed_files)

        app = web.Application()
        app.add_routes(
            [
                web.get("/", self.handle),
                web.get("/{folder}/{plugin_name}/{filename}", self.handle_files),
                web.get("/{folder}/{filename}", self.handle_files),
                web.get("/ws", self.handle_ws),
            ]
        )

        app.on_startup.append(self.start_background_tasks)
        app.on_cleanup.append(self.cleanup_background_tasks)
        web.run_app(app)


    async def handle(self, request):
        text = self.renderer.render(
            # plugins=plugin_configs,
            css_filelist=self.allowed_files,
            js_filelist=self.allowed_files
        )
        return web.Response(text=text, content_type="text/html")


    async def handle_files(self, request):
        filename = request.match_info.get("filename", "error")
        requested_folder = request.match_info.get("folder", "error")

        if requested_folder == "plugins":
            plugin_name = request.match_info.get("plugin_name", "error")
            filepath = os.path.join(requested_folder, plugin_name, filename)
        elif requested_folder == "web":
            filepath = os.path.join(requested_folder, filename)
        else:
            raise web.HTTPNotFound()

        if not filepath in self.allowed_files:
            raise web.HTTPNotFound()

        abs_path = os.path.realpath(filepath)
        # TODO: Does web.FileResponse do caching?
        return web.FileResponse(abs_path)


    async def handle_ws(self, request):
        self.logger.info("ws request: {}".format(request))
        ws = web.WebSocketResponse()
        self.ws_clients.add(ws)
        await ws.prepare(request)

        topic = "websocket/new_client"
        message = WebsocketRequest(topic, ws_id=id(ws))
        Topics.send_message(message)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data_dict = json.loads(msg.data)
                except Exception as e:
                    self.logger.info("error {} parsing message: {}".format(e, msg))
                    continue

                try:
                    plugin_name = data_dict["plugin_name"]
                    payload = data_dict["payload"]
                except KeyError:
                    self.logger.info("Keys plugin_name or payload not present in {}".format(data_dict))
                    continue

                ### debug code, send message to arbitrary receivers.
                if plugin_name == "debug":
                    message_destination = data_dict["message_destination"]
                    receiving_plugin = data_dict["receiving_plugin"]
                    if message_destination == "to_client":
                        m = WebsocketRequest(f"websocket/{receiving_plugin}/frontend", payload)
                        await self.send_topic_over_ws(m)
                        continue
                    elif message_destination == "to_server":
                        plugin_name = receiving_plugin
                    else:
                        raise Exception("no such destination:", message_destination)
                ### end debug code

                topic = "websocket/{}/backend".format(plugin_name)
                message = WebsocketRequest(topic, payload=payload, ws_id=id(ws))
                Topics.send_message(message)

            elif msg.type == web.WSMsgType.BINARY:
                self.logger.info("Not going to handle binary data.")
                continue

            elif msg.type == web.WSMsgType.CLOSE:
                break

        self.ws_clients.remove(ws)
        self.logger.info("removed ws client")
        return ws

    async def start_background_tasks(self, app):
        app["server_msg_loop"] = asyncio.create_task(self.event_loop())

        for plugin in self.plugins_list:
            app[plugin.name] = asyncio.create_task(plugin.event_loop())

    async def cleanup_background_tasks(self, app):
        app["server_msg_loop"].cancel()
        await app["server_msg_loop"]

        for plugin in self.plugins_list:
            app[plugin.name].cancel()
            await app[plugin.name]

    # === Messaging with Frontend ===

    async def send_topic_over_ws(self, message):
        # assumes topic format "websocket/<plugin_name>/frontend"
        plugin_name = message.topic.split("/")[1]
        data = message.payload

        # Converts message to format that is sent over ws. Could be beautified.
        json_str = json.dumps({
            "plugin_name": plugin_name,
            "payload": data
        })

        if message.ws_id == -1:
            for ws in self.ws_clients:
                # TODO: ws has a send_json method. Try that.
                await ws.send_str(json_str)
        else:
            ws_id_dict = {id(ws): ws for ws in self.ws_clients}
            if message.ws_id in ws_id_dict.keys():
                await ws_id_dict[message.ws_id].send_str(json_str)

