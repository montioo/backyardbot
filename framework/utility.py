#
# utility.py
# backyardbot
#
# Created: November 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import logging


async def log_coroutine_exceptions(awaitable, logger):
    """
    Exceptions in a coroutine can get unnoticed when the coroutine is
    started with asyncio.create_task(..). Wrap the coroutine in this function
    to log all exceptions.
    """
    try:
        await awaitable
    except Exception as e:
        logger.exception("Exception in coroutine:", e)


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
        # using the global application settings
        localization_dict.update(global_settings.get("localization", {}).get(language, {}))
        # using the plugin's settings
        localization_dict.update(plugin_settings.get("localization", {}).get(language, {}))

    return localization_dict


def create_logger(name, *config_dict):
    """
    Creates a logging object. Either uses the default configuration or a list
    of configuration dicts with decreasing priority. Config dict has to
    contain the key "logging" which holds another dict that holds the actual
    configuration. All parameters are optional. Recommendation for logger
    names of classes:
    `__name__ + "." + self.__class__.__name__`
    ```
    # Default config:
    config["logging"] = {
        "log_file": "byb.log",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_to_stream": True,
        "log_level_stream": "DEBUG",
        "log_to_file": True,
        "log_level_file": "DEBUG"
    }
    ```
    """

    log_config = {
        # default settings:
        "log_file": "byb.log",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_to_stream": True,
        "log_level_stream": "DEBUG",
        "log_to_file": True,
        "log_level_file": "DEBUG"
    }

    for config in reversed(config_dict):
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
