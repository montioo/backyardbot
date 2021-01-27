#
# renderer.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from jinja2 import Template
from jinja2 import Environment, meta
from .utility import create_logger
from collections import defaultdict


class Renderer:
    def __init__(self, plugin_manager, html_template, static_files):
        self.plugins = plugin_manager.get_plugin_list()
        self.ui_module_query = plugin_manager.calc_uimodule_parameter_list

        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name)

        self.css_files = [f for f in static_files if f.endswith(".css")]
        self.js_files = [f for f in static_files if f.endswith(".js")]

        with open(html_template) as f:
            self.main_template_str = f.read()

    def render(self, *args, **kwargs):
        """ Gives a list of plugins that are not explicitly mentioned in the template. """

        env = Environment()
        ast = env.parse(self.main_template_str)
        used_vars = meta.find_undeclared_variables(ast)
        self.logger.info(used_vars)
        plugin_names = {p.name for p in self.plugins}
        plugin_dict = {p.name: p for p in self.plugins}

        # plugins that are not listed in the template explicitly
        unlisted_plugins = plugin_names - used_vars
        listed_plugins = plugin_names - unlisted_plugins

        unlisted_renderers = {plugin_dict[up_name].render for up_name in unlisted_plugins}

        template_dict = {
            "stylesheets": self.css_files,
            "plugin_renderers": unlisted_renderers,
            "scripts": self.js_files
        }
        template_dict.update(kwargs)

        for ls_name in listed_plugins:
            template_dict[ls_name] = plugin_dict[ls_name].render

        # self.logger.debug(template_dict)

        html_template = Template(self.main_template_str)
        return html_template.render(template_dict)

        # Will not perform a check to see whether the plugin was explicitly used:
        # plugin_configs = self.ui_module_query()
        # html_template = Template(self.main_template_str)
        # template_dict = {
        #     "stylesheets": self.css_files,
        #     "scripts": self.js_files,
        #     # TODO: Better naming?
        #     "plugin_renderers": [p.render for p in self.plugins],
        #     "plugins": plugin_configs
        # }
        # template_dict.update(kwargs)
        # return html_template.render(template_dict)
