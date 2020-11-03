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
from framework.utility import create_logger


def main():
    logger_name = __name__
    top_logger = create_logger(logger_name)

    settings_file = "byb/settings.json"
    if len(sys.argv) < 2:
        top_logger.info("no settings file given, using default: byb-repo/byb/settings.json")
    else:
        settings_file = sys.argv[1]

    try:
        _ = open(settings_file)
    except FileNotFoundError:
        top_logger.error("Didn't find the specified config file: {}".format(settings_file))
        return

    # TODO: Create some form of default settings file.
    Database.set_db_path("byb/db.json")

    # TODO: Load this from settings file.
    pluginManager = PluginManager("plugins/")

    Server(settings_file, pluginManager)


if __name__ == "__main__":
    main()