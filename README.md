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

```json
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

```json
[
    {

    }
]
```