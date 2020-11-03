# framework Documentation

This folder holds the components of the framework that enables building a plugin based application like backyardbot.

It is developed together with backyardbot but aims to be a generic framework that can be utilized for other systems as well.


## Plugin System

TODO



### Plugin loop

A plugin might want to do some recurring computation, e.g. read a sensor.

One option to make this happen is to have some kind of `self.spin()` at the end of the plugin's init method. Like with ROS nodes the plugin either calls this to do nothing else or it can set up a loop to compute stuff.

All of this should be written with asyncio.


### Plugin settings


#### Localization

TODO: Extend localization system to deal with units as well (meters, miles, ...)

The plugin system supports multiple languages. The plugin's `settings.json` may contain an object titled *localization* which contains texts for different UI elements in the frontend.

```js
// plugin's settings.json:
{
    "localization": {
        "en": {
            "btn_01_title": "String for the button",
            "info_text": "Static text to display somewhere"
        },
        "de": {
            "btn_01_title": "Zeichenkette für den Button",
            // ...
        }
        // ...
    }
    // ...
}
```

Inside the `.html` template of a plugin, they are accessed by

```html
<i>{{ localization["info_text"] }}</i>
```

The global `settings.json` of the server system will determine the language to use. In the *general* object, a single string or a list of strings can be set as the value of the *language* key.

```js
// global settings.json for all of the system:
{
    "general": {
        "language": ["en", "de"]  // or just "en"
        // ...
    }
    // ...
}
```

The order of the languages determines their priority, first one is highest priority. Should a term not be available in a language, its translation from the next priority will be used.


#### Logging

The utility file offers a function `create_logger(name, *config_files)` which will return a readily configured logging object. The logging preferences are configured from default values which are given by the following parameters:

```js
// default settings:
{
    "logging": {
        "log_file": "byb.log",
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_to_stream": true,
        "log_level_stream": "DEBUG",
        "log_to_file": true,
        "log_level_file": "DEBUG"
    }
}
// TODO: Set different default log file name.
```

`create_logger(..)` accepts a list of configuration dicts which are ordered in descending priority and each hold a key *logging* under which the above preferences may be listed. Any values contained in these dicts will update the default logging options for the currently created logger instance. Different logging configurations may occur from a system level log file and additional log files for specific modules.

The log levels are the same ones present in Python's built-in logging module.

A logger can have a name which is used in the default logging format. A recommended name for classes that use a logger is:

```python
logger_name = __name__ + "." + self.__class__.__name__
```