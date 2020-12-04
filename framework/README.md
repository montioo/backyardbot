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

##### Defining Localization Data

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
On top of that, the global settings can also contain localization data. Those will be merged with the data given in a plugin's `settings.json`, in the sense that the plugin's localization data can overwrite the data that is provided in the global settings.

```js
// global settings.json for all of the system:
{
    "general": {
        "language": ["en", "de"]  // or just "en"
        // ...
    }
    // ...
    "localization": {
        "en": {
            // ...
        }
        // ...
    }
}
```

The order of the languages determines their priority, first one is highest priority. Should a term not be available in a language, its translation from the next priority will be used.

##### Accessing Localization Data

- In the plugin's python code: Using the dict `self.localization`, e.g. `self.localization["weekdays"]`
- In the plugin's html template: Using the dict `localization`, e.g. `{{ localization["weekdays"] }}`
- So far, building custom js objects in the html template is the preferred way of passing localization data to the frontend.

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


#### Messages and Topics

A `Message` instance can be sent by the `Topic` class. It will be send to all registered instances but only some may react (i.e. decide to enqueue it in their message buffer).

Reserved topics:
- `websocket/<plugin_name>/backend` : messages to a plugin's handler from the frontend
- `websocket/<plugin_name>/frontend` : ...
- `websocket/new_client` : Will be sent out by the server as a new js client connects. Contains the id of the new ws object so that plugins have the ability to send a message to only the new client.

maybe `websocket/frontend/<plugin_name>` and `websocket/backend/<plugin_name>` is better as the frontend stuff is handled by the js code which is not executed 'in the same place' as the python code.


TODO: The plugins don't need to know about the server as they can send data using the topics and the stuff will be forwarded to the server and from there to the frontend of the website.


## Server


### Topic <--> Websocket

As a new websocket client connects to the server, all plugins will have the opportunity to send a message to only this individual new client. The server will inform all plugins about the new websocket client and include the client's id in this notification.

A plugin can send a message over a topic to the server which will then be forwarded to all ws clients (broadcast) or include a specific id to only forward the message to on ws client.

Topics to address the server:

`websocket/<plugin_name>/frontend`: The server will forward messages received on that topic to the websocket client(s)

If no receiver is given in the Message description (receiver is `None`), the message will be forwarded to all websocket frontends. If a receiver is given, the message will only be forwarded to this specific websocket client.

```
 browser  --+             +--------+          +-- plugin
            |  websocket  |        |  topics  |
 browser  --+-------------+ Server +----------+-- plugin
            |             |        |
 browser  --+             +--------+
```

The communication system is shown in the schematic above. The right part of the system is written in Python and plugins and the server can communicate with each other using topics. On top of that, the server opens up the possibility to convert topic messages to messages sent over websockets. The plugins don't need to know about this conversion and for a plugin the communication with it's frontend counterparts is equivalent to the communication with another part of the system.

TODO: Message structure for the different communication types?