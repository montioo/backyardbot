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
from .plugin_manager import PluginManager


def load_allowed_files(settings: dict):
    allowed_files = []
    for file_list in ["static_web_files", "template_web_files"]:
        # allowed_files |= set(glob.glob(settings.get("application", {}).get(file_list, [])))
        files = settings.get("application", {}).get(file_list, [])
        for f in files:
            if f not in allowed_files:
                allowed_files.append(f)

    print("allowed_files 1", allowed_files)
    return allowed_files

def get_html_template_file(settings: dict):
    return settings.get("application", {}).get("template_index", "web/index.html")


class Server:

    def __init__(self, settings_file, plugin_manager):
        self.ws_clients = set()

        settings = json.load(open(settings_file))
        self.allowed_files = load_allowed_files(settings)

        self.plugins_list = plugin_manager.get_plugin_list()
        self.plugins_dict = plugin_manager.get_plugin_dict()

        self.plugin_manager = plugin_manager
        for plugin in self.plugins_list:
            plugin.register_server(self)
            self.allowed_files += plugin.css_files()
            self.allowed_files += plugin.js_files()

        html_template_file = get_html_template_file(settings)
        self.renderer = Renderer(self.plugins_list, html_template_file, self.allowed_files)

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
        plugin_configs = self.plugin_manager.calc_uimodule_parameter_list()
        text = self.renderer.render(
            plugins=plugin_configs,
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
        print(request)
        ws = web.WebSocketResponse()
        self.ws_clients.add(ws)
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data_dict = json.loads(msg.data)
                except Exception as e:
                    print("error", e, "parsing message:", msg)
                    continue

                plugin_name = data_dict["plugin_name"]
                payload = data_dict["payload"]

                ### debug code, send message to arbitrary receivers.
                if plugin_name == "debug":
                    message_destination = data_dict["message_destination"]
                    receiving_plugin = data_dict["receiving_plugin"]
                    if message_destination == "to_client":
                        await self.send_to_clients(payload, receiving_plugin)
                        continue
                    elif message_destination == "to_server":
                        plugin_name = receiving_plugin
                    else:
                        raise Exception("no such destination:", message_destination)
                ### end debug code

                if plugin_name in self.plugins_dict:
                    self.plugins_dict[plugin_name].message_from_client(payload)
                else:
                    print("Received message for unknown plugin:", plugin_name)

            elif msg.type == web.WSMsgType.BINARY:
                print("Not going to handle binary data.")
                continue

            elif msg.type == web.WSMsgType.CLOSE:
                break

        self.ws_clients.remove(ws)
        print("removed client")
        return ws


    async def start_background_tasks(self, app):
        # app["ws_broadcast"] = asyncio.create_task(self.periodic_ws_broadcast())

        for plugin in self.plugins_list:
            app[plugin.name] = asyncio.create_task(plugin.event_loop())

    async def cleanup_background_tasks(self, app):
        # app["ws_broadcast"].cancel()
        # await app["ws_broadcast"]

        for plugin in self.plugins_list:
            app[plugin.name].cancel()
            await app[plugin.name]

    async def send_to_clients(self, data, name):
        json_str = json.dumps({
            "plugin_name": name,
            "payload": data
        })
        await self.ws_broadcast(json_str)

    async def ws_broadcast(self, msg):
        for ws in self.ws_clients:
            await ws.send_str(msg)

    async def periodic_ws_broadcast(self):
        while True:
            await asyncio.sleep(8)
            await self.ws_broadcast("broadcast test")
