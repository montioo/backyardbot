# backyardbot

Automatic gardening server that keeps plants alive. Comes with a plugin system to improve expandability and adapt to every garden or balcony.


## Dependencies:

- Tornado
- TinyDB


## Development Info

Include this projects root folder in your system's Python path to use the plugin modules from within plugin implementations.

This can be done by executing `update_pythonpath.sh`


# Documentation:

backyardbot consists of several plugins and an architecture definition that enables those plugins to work together to create an application for a specific use-case.

The architecture of the components that are specific to backyardbot are described below. It uses a framework that supplies functionality for a plugin based system.


## Dataflow:

A class can store it's own data in a persistent way by creating a table in the database.

A table can hold data that only a single class needs (e.g. which sprinkler is currently active) as well as data that might interest other entities as well, e.g. the number of sprinkler and their properties.


## Further Concepts:

### Zones and Actuators:

Watering of plants is broken down into zones and actuators.

- *Actuators* are components that are physically controllable like a pump or a magnetic valve.
- *Zones* are areas which can not be broken down further to water parts of them individually, e.g. a bed that is watered by one sprinkler. It may have several plants but the one sprinkler can either be on or off, meaning one can't control that the left flower should be watered and the right one shouldn't.

In most cases, the number of *Actuators* and *Zones* will match and each *Zone* has one *Actuator*. Some rare cases might be different though, as there are systems where one *Actuator* can control several *Zones*.

In general: #*Zones* >= #*Actuators*


## Database Tables:

### Time Schedule - `time_schedule_table`:

```js
[
    {
        "time_hh": Int,
        "time_mm": Int,
        "duration": Int,    // seconds
        "weekdays": [Int],  // Mon = 0, ...
        "zone": [Int]       // watering zones
    },
    ...
]
```


### Watering Zones - `sprinkler_info_table`:

For the most part, the numbers of actuators and zones match. If no zones are defined, the system will assume that this is the case and associate each actuator with an equally named zone.
Public for all of the system are the zones
The zones are public for all components of the system and available in the `sprinkler_info_table`. The underlying mapping from *Zone X should be watered* -> *This means Actuator Y has to be triggered* -> *Actuator Y is connected to gpio Z and controlled in this and that way* is done by the Actuator plugin and of no interest to the rest of the system.

The Actuation plugin will take care of zones and actuators. There is one configuration that is global and highlights the structure of all available actuators and on top of that, the actuation module holds a private configuration which includes information like the GPIO pin to which an actuator is attached.

```js
// Zones:
[
    {
        "zone_id": Int,
        "zone_name": str
    }
]
```


This is an example of the data that the actuator plugin might hold.
```js
"actuators":
    [
        {
            "actuator_name": str,
            "python_class": str,   // not sure if this is the best way (class name)
            "managed_zones": [Int],
            "zone_specific_parameters": {
                "channel_count": Int,
                "cooldown_duration": Int,
                "use_dummy_gpio": Bool,
                "gpio_pin": Int,
                "run_watering_thread": Bool,
                "channel_state_file": str
            }

        }
    ]
```

Data shared between plugins:
- timetable (maintained by tt plugin but readable by everybody)
- zones (some for actuator plugin)


Future features:
- Sensors:
  - read data periodically (or by demand?) and write it to DB
- Watering duration based on sensor readings:
  - Using this can be simple because values can expose a scalar value
  - *Modifier* takes sensor reading and planned watering duration and outputs new duration
  - => how to tweak the modifier? I guess this would be part of the timetable plugin?
  - Or if advanced *Modifiers* should be possible (chaining, multi-input, whatever) some
    sort of advanced UI? But still can stay with tt plugin I'd say.
- Telegram Plugin? Can receive cmds and send system status via telegram.
  - how to access the system state?
  - => every plugin can expose some data (which data this is might be listed in the
    plugins definition) which other plugins can access? The plugin superclass would make
    them accessible via rpc or another communication technique. How did requesting
    information specifically work in ROS? Advance a plugin's settings.json or the plugins
    super class with a way for the plugin to mark some info publicly available.
  - => also maybe a .summary for a summary of some sort of each plugin?

Needs:
- some sort of system similar to rpc, e.g. read data from sensor X and return data.
