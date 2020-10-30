#
# jinja2_plugin_sys.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

"""
Requirements:

- [x] Include templates from subfolders and have their contents
    generated from python scripts.
    => yes, this also works. Atm need to generate a new template for
    this. Maybe there is a cleaner solution.
- [x] Include additional files (css and js) from arbitrary folders.
    => as long as the relative template path is accessible by
    the webserver, this works.
- [x] Don't be a pain in the ass
    => so far, it isn't

- [ ] How to integrate this with aiohttp?
"""

from jinja2 import Template
from jinja2 import Environment, meta


plugin_template_str = """
<div id="{{ v }}">
    Hello from {{ name }}
</div>
"""

class Plugin:
    def __init__(self, name, val):
        self.v = val
        self.name = name

    def render(self):
        # set up an own Template instance?
        global plugin_template_str
        t = Template(plugin_template_str)
        # return u"plugin rendered {}".format(self.v)
        return t.render(v=self.v, name=self.name)

    def css_files(self):
        # code like this could be placed inside the Plugin
        # super class which would also take a bunch of work off
        # of the plugin loader.
        return ["important.css"]

    # TODO: Using something similar to this could avoid using () in the templates
    # def __repr__(self):
    #     return self.render()

    # def js_files(self):
    #     pass

p1 = Plugin("p1", 6)
p2 = Plugin("p2", 9)
p3 = Plugin("p3", 3)


"""
Central question:
- [x] How to best determine a plugin's position? This has
    to be hardcoded in the html template, I guess.
    => Template sets the positions for plugins but there
    is also a variable that contains a list of activated
    plugins that weren't used elsewhere in the code.
"""

main_template_str = """
<head>
    {% for css_file in css_files %}
        <link rel="stylesheet" href="{{ css_file }}">
    {% endfor %}
</head>
<body>

    <div class="template_box">
        {{ p2() }}
    </div>

    {% for plugin in plugin_renderers %}
        {{ plugin() }}
    {% endfor %}

</body>
"""

class Renderer:
    def __init__(self, plugins):
        self.plugins = plugins
        self.css_files = set()

        for plugin in self.plugins:
            self.css_files |= set(plugin.css_files())

    def render(self):
        global main_template_str
        html_template = Template(main_template_str)
        # TODO: How to not only iterate over plugin list but set
        # them by name? Is there a way despite editing the template?
        # e.g. changing the plugin order online (in the frontend) and
        # then saving this somewhere?
        template_dict = {
            "css_files": self.css_files,
            "plugin_renderers": [p.render for p in self.plugins]
        }
        return html_template.render(template_dict)


# Renderer2 approach:
# - Subclass Template to get the function calls that are in there.
#   This should enable me to come up with a list `plugins` that holds
#   the plugins that weren't used in the code elsewhere.
# similar to this:
# >>> from jinja2 import Environment, meta
# >>> ts = '<div id="{{ meinevar.val }}">'
# >>> env = Environment()
# >>> ast = env.parse(ts)
# >>> meta.find_undeclared_variables(ast)
# {'meinevar'}

class Renderer2(Renderer):

    def render(self):
        """ Gives a list of plugins that are not explicitly mentioned in the template. """
        global main_template_str
        env = Environment()
        ast = env.parse(main_template_str)
        used_vars = meta.find_undeclared_variables(ast)
        print(used_vars)
        plugin_names = {p.name for p in self.plugins}
        plugin_dict = {p.name: p for p in self.plugins}

        # plugins that are not listed in the template explicitly
        unlisted_plugins = plugin_names - used_vars
        listed_plugins = plugin_names - unlisted_plugins

        unlisted_renderers = {plugin_dict[up_name].render for up_name in unlisted_plugins}

        template_dict = {
            "css_files": self.css_files,
            "plugin_renderers": unlisted_renderers
        }

        for ls_name in listed_plugins:
            template_dict[ls_name] = plugin_dict[ls_name].render

        print(template_dict)

        html_template = Template(main_template_str)
        return html_template.render(template_dict)


if __name__ == "__main__":
    r = Renderer2([p1, p2, p3])

    print(r.render())
