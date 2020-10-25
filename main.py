#
# main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from plugins.timetable.plugin_main import TimetablePlugin
import tornado.web
import tornado.websocket
import tornado.ioloop
import os
import json


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WsHandler(tornado.websocket.WebSocketHandler):
    client_list = set()
    plugins = {}

    def open(self):
        WsHandler.client_list.add(self)

    def on_close(self):
        WsHandler.client_list.remove(self)

    def on_message(self, message):
        try:
            j = json.loads(message)
        except Exception as e:
            print("error parsing message:", message)
            print(e)
            return

        print("got msg", j, "type:", type(message))
        plugin_name = list(j.keys())[0]
        WsHandler.plugins[plugin_name].message_from_client(j[plugin_name])

    @classmethod
    def send_updates(cls, data, name):
        d = json.dumps({name: data})
        for client in cls.client_list:
            try:
                client.write_message(d)
            except:
                print("Error sending a message.")

class Application(tornado.web.Application):
    def __init__(self, ui_modules):
        handlers = [
            (r"/", IndexHandler),
            (r"/websocket", WsHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "template"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules=ui_modules
        )
        super().__init__(handlers, **settings)

class DummyServer:
    def send_to_clients(self, data, name):
        WsHandler.send_updates(data, name)


def load_plugins():
    # look at all plugins in plugins/ dir
    # either load all of them
    # or use config file to load plugins
    # but still: then I would need a global config file and a config file for each plugin?
    pass

def main():
    ds = DummyServer()
    timetablePlugin = TimetablePlugin(ds, "TimetablePlugin")
    WsHandler.plugins["a"] = timetablePlugin  # more of a proof of concept
    ui_modules = {"TimetablePlugin": timetablePlugin.ui_module}
    # TODO: building something like this should be done with a plugin manager

    app = Application(ui_modules)
    app.listen(8888)

    # use this to run other functions that are awaitable
    # tornado.ioloop.IOLoop.current().run_sync(awaitable_func)

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()