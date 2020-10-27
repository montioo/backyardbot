#
# main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from plugin import BybPluginUIModule
from plugin_manager import PluginManager
import tornado.web
import tornado.websocket
import tornado.ioloop
import os
import json


class WsHandler(tornado.websocket.WebSocketHandler):
    client_list = set()
    # TODO: Store the clients at some other place.
    plugins = {}

    def open(self):
        WsHandler.client_list.add(self)

    def on_close(self):
        WsHandler.client_list.remove(self)

    def on_message(self, message):
        try:
            data_dict = json.loads(message)
        except Exception as e:
            print("error parsing message:", message)
            print(e)
            return

        plugin_name = data_dict["plugin_name"]
        payload = data_dict["payload"]

        ### debug code
        if plugin_name == "debug":
            message_destination = data_dict["message_destination"]
            receiving_plugin = data_dict["receiving_plugin"]
            if message_destination == "to_client":
                WsHandler.send_updates(payload, receiving_plugin)
                return
            elif message_destination == "to_server":
                plugin_name = receiving_plugin
            else:
                raise Exception("no such destination:", message_destination)
        ### end debug code

        print(WsHandler.plugins)
        if plugin_name in WsHandler.plugins:
            WsHandler.plugins[plugin_name].message_from_client(payload)
        else:
            print("Received message for unknown plugin:", plugin_name)

    @classmethod
    def send_updates(cls, data, name):
        d = json.dumps({
            "plugin_name": name,
            "payload": data
        })

        for client in cls.client_list:
            try:
                client.write_message(d)
            except:
                print("Error sending a message.")

class IndexHandler(tornado.web.RequestHandler):
    # TODO: Move this to another place
    pluginmanager = None

    def get(self):
        # plugin_list = IndexHandler.pluginmanager.calc_uimodule_parameter_list()
        plugin_configs, css_filelist, js_filelist = IndexHandler.pluginmanager.calc_uimodule_parameter_list()
        self.render("index.html", plugins=plugin_configs, css_filelist=css_filelist, js_filelist=js_filelist)


class DeepStaticFileHandler(tornado.web.StaticFileHandler):
    """ Subclass of the tornado.web.StaticFileHander which also serves files multiple directories deep. """
    # TODO: Override initialize(..) to not need the static path. Get it from global config file.
    #  https://www.tornadoweb.org/en/stable/_modules/tornado/web.html#StaticFileHandler

    def get(self, *args, **kwargs):
        uri = self.request.uri[1:]
        # TODO: Only serve file if it was specified in a plugin's settings.json
        filepath = os.path.join(os.path.abspath("."), uri)
        return super().get(filepath)


class Application(tornado.web.Application):
    def __init__(self, ui_modules):
        handlers = [
            (r"/", IndexHandler),
            (r"/websocket", WsHandler),
            (r"/plugins/(.*)/(.*)\.(css|js)", DeepStaticFileHandler, {"path": "/Users/monti/Documents/ProjectsGit/byb-github"})
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "template"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules=ui_modules,
            debug=True  # no caching, etc.
        )
        super().__init__(handlers, **settings)

class DummyServer:
    def send_to_clients(self, data, name):
        WsHandler.send_updates(data, name)


class Byb:
    # TODO: e.g. like this:
    plugins = {}
    pluginmanager = {}

    def __init__(self):
        pass


def main():
    ds = DummyServer()
    pluginManager = PluginManager("plugins", ds)
    IndexHandler.pluginmanager = pluginManager
    WsHandler.plugins = pluginManager.get_plugin_dict()

    ui_module = {"BybPluginUIModule": BybPluginUIModule}
    app = Application(ui_module)
    app.listen(8888)

    # use this to run other functions that are awaitable
    # tornado.ioloop.IOLoop.current().run_sync(awaitable_func)

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()