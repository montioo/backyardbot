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
from collections import namedtuple


PluginInfo = namedtuple("PluginInfo", "html_template_path css_filepath_list js_filepath_list")


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
            # TODO: Clean up, this surely is not all needed anymore...
            self.plugin_name = plugin_settings_path.split("/")[-2]
            self.settings = json.load(open(plugin_settings_path))
            plugin_class_name = self.settings["class_name"]
            self.plugin_dir = os.path.dirname(plugin_settings_path)
            plugin_module_file = os.path.join(self.plugin_dir, self.settings["plugin_main"])

            # Loading class from module. What happened to the python mantra "There is one obvious way"?
            plugin_module = f"{self.plugin_name}.{plugin_class_name}"  # import statement
            spec = importlib.util.spec_from_file_location(plugin_module, plugin_module_file)
            imported_plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(imported_plugin_module)
            self.PluginClass = getattr(imported_plugin_module, plugin_class_name)

            # self.plugin_info = PluginInfo(html_template_path, css_filepath_list, js_filepath_list)
            self.pluginInstance = None

        def calc_uimodule_parameters(self):
            dynamic_info = {
                "plugin_name": self.plugin_name,
                "values": self.pluginInstance.calc_render_data()
            }
            return dynamic_info

        @classmethod
        def is_plugin_loadable(cls, plugin_settings_path):
            """
            Plugin's settings can specify the option `load_plugin`. If it is
            not set or set to `True`, the plugin will be loaded and used by
            backyardbot. Otherwise it will not ignored.
            """
            settings = json.load(open(plugin_settings_path))
            return settings.get("load_plugin", True)

    def __init__(self, plugin_folder):
        plugin_dirs = glob.glob(os.path.join(plugin_folder, "*", "settings.json"))
        self.plugin_loaders = [self.PluginLoader(p) for p in plugin_dirs if self.PluginLoader.is_plugin_loadable(p)]

        self.plugin_dict = {}
        for loader in self.plugin_loaders:
            name, pluginClass = loader.plugin_name, loader.PluginClass
            loader.pluginInstance = pluginClass(name, os.path.join(loader.plugin_dir, "settings.json"))
            self.plugin_dict[name] = loader.pluginInstance

    def get_plugin_dict(self):
        return self.plugin_dict

    def get_plugin_list(self):
        return [self.plugin_dict[key] for key in self.plugin_dict.keys()]

    def calc_uimodule_parameter_list(self):
        plugin_individual_configs = []

        for loader in self.plugin_loaders:
            # TODO: Don't query the loader but the plugin itself?
            individual_info = loader.calc_uimodule_parameters()
            plugin_individual_configs.append(individual_info)

        return plugin_individual_configs
