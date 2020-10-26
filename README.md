# backyardbot

Automatic gardening server that keeps plants alive. Comes with a plugin system to improve expandability and adapt to every garden or balcony.


## Problems with `tornado`:

One UIModule subclass is only queried once for css and js files even though the module is used multiple time. This is by design of tornado and makes sense for the use case for which tornado was built, but is a problem for my envisioned plugin architecture.

Possible workaround: The UIModule subclass would need to return all js and css files (for all plugins) at once.

Or: Look at other libraries.


## Development Info

Include this projects root folder in your system's Python path to use the plugin modules from within plugin implementations.

This can be done by executing `update_pythonpath.sh`
