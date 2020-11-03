#
# utility.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import logging


def pick_localization(plugin_settings, global_settings):
    """
    Builds the localization dict for the front ends with different languages.
    Accepts a list from the global settings file with decreasing priorities.
    Defaults to english (en) and will return an empty dict if no localization
    options are given.
    """
    language_priorities = list(global_settings.get("general", {}).get("language", "en"))
    localization_dict = {}

    for language in reversed(language_priorities):
        localization_dict.update(plugin_settings.get("localization", {}).get(language, {}))

    return localization_dict


def create_logger(name, *config_files):
    """
    Creates a logging object. Either uses the default configuration or a list
    of configuration files with decreasing priority.
    Recommendation for logger names of classes:
    `__name__ + "." + self.__class__.__name__`
    """

    # default settings:
    log_config = {
        "log_file": "byb.log",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_to_stream": True,
        "log_level_stream": "DEBUG",
        "log_to_file": True,
        "log_level_file": "DEBUG"
    }

    for config in reversed(config_files):
        log_config.update(config.get("logging", {}))

    logging_levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "notset": logging.NOTSET
    }

    stream_level = logging_levels.get(log_config["log_level_stream"].lower(), logging.DEBUG)
    file_level = logging_levels.get(log_config["log_level_file"].lower(), logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(log_config["log_format"])

    if log_config["log_to_file"]:
        fh = logging.FileHandler(log_config["log_file"])
        fh.setLevel(file_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if log_config["log_to_stream"]:
        sh = logging.StreamHandler()
        sh.setLevel(stream_level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger