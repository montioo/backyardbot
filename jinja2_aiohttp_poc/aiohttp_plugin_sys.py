#
# aiohttp_plugin_sys.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

"""
Requirements:

- [x] Serve files from a list of allowed files
  => serving files works with a path and the a handler has to determine
  whether I want to server the requested files.
- [x] Websockets: maintain list off all clients and broadcast to all of them
- [x] Render templates and send them.
"""

from aiohttp import web
import asyncio
from random import randint
from jinja2_plugin_sys import Renderer2, p1, p2, p3


class Plugin:
    def __init__(self, name):
        self.name = name
        self.server = None

    def register_server(self, server):
        self.server = server

    async def spin_once(self):
        await asyncio.sleep(5)

    async def spin(self):
        while True:
            await asyncio.sleep(5)

    async def event_loop(self):
        raise NotImplementedError("no event loop defined")


class SensorPlugin(Plugin):
    def __init__(self, name):
        super().__init__(name)

    async def event_loop(self):
        while True:
            # could write it to a DB but going to send it
            sensor_reading = 23
            await self.server.ws_broadcast(sensor_reading)
            await self.spin_once()


class Server:

    def __init__(self, plugins):
        self.ws_clients = set()
        self.plugins = plugins
        for plugin in self.plugins:
            plugin.register_server(self)

        self.renderer = Renderer2([p1, p2, p3])

        app = web.Application()
        app.add_routes(
            [
                web.get("/", self.handle),
                web.get("/plugins/{folder}/{filename}", self.handle_files),
                web.get("/ws", self.handle_ws),
            ]
        )

        app.on_startup.append(self.start_background_tasks)
        app.on_cleanup.append(self.cleanup_background_tasks)
        web.run_app(app)

    async def handle(self, request):
        # TODO: Render template instead
        text = "<html><head><title>hello</title></head><body>world</body></html>"
        text = self.renderer.render()
        return web.Response(text=text, content_type="text/html")

    async def handle_files(self, request):
        # not using web.static(..) to serve files because it will serve full direcotries
        #  and only a selection of files from a directory should be served.
        plugin_folder = request.match_info.get("folder", "error")
        filename = request.match_info.get("filename", "error")
        if plugin_folder == "illegal":
            raise web.HTTPNotFound()
        print(plugin_folder, filename)
        # TODO: Only serve file if it's in the list of allowed files.
        return web.FileResponse("/Users/monti/Documents/ProjectsGit/byb-github/static/overlay.css")

    async def handle_ws(self, request):
        print(request)
        ws = web.WebSocketResponse()
        self.ws_clients.add(ws)
        await ws.prepare(request)

        async for msg in ws:
            print("new message:", msg)
            if msg.type == web.WSMsgType.TEXT:
                await ws.send_str(f"Hello, {msg.data}")
            elif msg.type == web.WSMsgType.BINARY:
                await ws.send_bytes(msg.data)
            elif msg.type == web.WSMsgType.CLOSE:
                break

        self.ws_clients.remove(ws)
        print("removed client")
        return ws

    async def start_background_tasks(self, app):
        app["ws_broadcast"] = asyncio.create_task(self.periodic_ws_broadcast())

        for plugin in self.plugins:
            app[plugin.name] = asyncio.create_task(plugin.event_loop())

    async def cleanup_background_tasks(self, app):
        app["ws_broadcast"].cancel()
        await app["ws_broadcast"]

        for plugin in self.plugins:
            app[plugin.name].cancel()
            await app[plugin.name]

    async def ws_broadcast(self, msg):
        for ws in self.ws_clients:
            await ws.send_str(f"Hello client, {msg}")

    async def periodic_ws_broadcast(self):
        while True:
            await asyncio.sleep(8)
            await self.ws_broadcast("what up")

plugins = [
    SensorPlugin("sensor plugin")
]

Server(plugins)