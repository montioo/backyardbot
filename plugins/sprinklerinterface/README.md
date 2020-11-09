# Sprinkler Interface Plugin for Byb

## Plugin Architecture (WIP)

```
 Input
   |     Message with
   |  Zones and Durations
   |
   v
 +-------------------------+
 |         Plugin          |
 | Maps zones to actuators |
 |    Maintains the UI     |
 +-------------------------+
    |        |        |
    |        |        .
    |        v
    |   +-------------------+
    |   |    Actuator 2     |
    |   | manages Zones 2-4 |
    |   +-------------------+
    v
 +-------------------+
 |    Actuator 1     |
 |   manages Zone 1  |
 +-------------------+
```

Naming:
- Should this plugin really be called SprinklerInterface? The Actuators are actually interfacing with the sprinklers.

Questions:
- How to handle actuator availability? Examples:
  - GardenaSixWay: One actuator, six zones, only one active at a time
  - Magnetic valves: One actuator-instance, multiple zones, all active at once.

Have zones that can not be active at the same time managed by one actuator.

So for a bunch of magnetic valves, there would be multiple actuator instances. But one may combine them into one instance if the water pressure is not sufficient to have them all operate at the same time?

Maybe the common interface should just be:
- Give a bunch of zones and durations to an actuator
- Query the current state from this actuator

An actuator doesn't need to be referenced directly but only the zones are known throughout the system.

**Next AIs:**
- [ ] How to deal with actuator definition? Static definition in a config file (plugin's `settings.json`) or in a database (which could potentially be adjusted at runtime with simple controls from the frontend)?


## Zone Layout Database

Since other plugins are interested in the zones that are available (or at least in the list of zones), there has to be a way to have those information accessible throughout the system.

BUT: This may be something that is not only related to this plugin but is important to the whole backyardbot and thus should be defined in the byb docs?
