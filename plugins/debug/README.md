# debug Plugin for Byb

This plugin is developed for debugging purposes. The server recognizes this plugin's name (debug) and offers some special functionality while handling the message.

Below is the special `json` format which the server receives.

```json
{
    "plugin_name": "debug",
    "payload": {},

    "message_destination": "to_client",
    "receiving_plugin": "another plugin's name"
}
```

As for usual plugins, it has the fields `plugin_name` and `payload` which hold the name of the plugin that sent the message and the payload it wants to transmit, respectively.

The debug plugin has the ability to send messages to whichever plugin it likes. As the server recognizes the plugin name *debug*, it will start to process another two parameters: `message_destination` and `receiving_plugin`. The latter determines the name of the plugin that will receive this message. The parameters `message_destination` indicates whether the server's backend should forward the message to a plugin's front- or backend. It can have the values `to_client` and `to_server`.

