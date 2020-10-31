#
# main.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import sys
from framework.main import Server
from framework.plugin_manager import PluginManager
from framework.memory import Database


def main():
    settings_file = "byb/settings.json"
    if len(sys.argv) < 2:
        print("no settings file given, using default:")
        print("   byb-repo/byb/settings.json")
    else:
        settings_file = sys.argv[1]

    try:
        _ = open(settings_file)
    except FileNotFoundError:
        print("Didn't find the specified config file:", settings_file)
        return

    # TODO: Create some form of default settings file.
    Database.set_db_path("byb/db.json")

    # TODO: Load this from settings file.
    pluginManager = PluginManager("plugins/")

    Server(settings_file, pluginManager)


if __name__ == "__main__":
    main()