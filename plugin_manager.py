#
# plugin_manager.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

import glob
import os
import importlib.util
import json


class PluginManager:
    """
    Tasks of the PluginManager:
    - Discover plugins
    - Instantiate plugins
    - Generate list of Plugins for templates:
      1. includes plugin's path
      2. Query plugin instances for data for the template data
    - build dict with plugin names

    *Note:* For now, PluginManager will load all available plugins.
    """

    class PluginLoader:
        """ Takes the path to a plugin and collects information about this plugin. """
        def __init__(self, plugin_settings_path):
            """ Loads a plugin and stores info on its location but will not instantiate it yet."""
            self.plugin_name = plugin_settings_path.rsplit("/")[-2]
            self.settings = json.load(open(plugin_settings_path))
            plugin_class_name = self.settings["class_name"]
            self.plugin_dir = os.path.dirname(plugin_settings_path)
            plugin_module_file = os.path.join(self.plugin_dir, self.settings["plugin_main"])

            # Loading class from module. What happened to the python mantra "There is one obvious way"?
            plugin_module = "{}.{}".format(self.plugin_name, plugin_class_name)
            spec = importlib.util.spec_from_file_location(plugin_module, plugin_module_file)
            imported_plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(imported_plugin_module)
            self.PluginClass = getattr(imported_plugin_module, plugin_class_name)

            self.PluginInstance = None

        def get_plugin_settings(self):
            return self.settings.get("plugin_settings", None)

        def calc_uimodule_parameters(self):
            return {
                "plugin_dir": self.plugin_dir,
                "plugin_name": self.plugin_name,
                "values": self.PluginInstance.calc_render_data()
            }

    def __init__(self, plugin_folder, server):
        self._plugin_path = os.path.realpath(plugin_folder)
        plugin_dirs = glob.glob(os.path.join(self._plugin_path, "*", "settings.json"))
        self.plugin_loaders = [self.PluginLoader(p) for p in plugin_dirs]

        self.plugin_dict = {}
        for loader in self.plugin_loaders:
            name, pluginClass = loader.plugin_name, loader.PluginClass
            settings = loader.get_plugin_settings()
            # self.plugin_dict[name] = pluginClass(name, settings, server)
            loader.PluginInstance = pluginClass(name, settings, server)

    def get_plugin_dict(self):
        return self.plugin_dict

    def calc_uimodule_parameter_list(self):
        return [loader.calc_uimodule_parameters() for loader in self.plugin_loaders]



