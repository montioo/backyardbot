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


## Communication between Backend and Frontend

All messages need to follow a certain structure, regardless of whether they are sent from the frontend to the backend or vice versa.

```js
{
    "command": String,
    "payload": Object
}
```

The receiver uses the command field to determine what kind of action should be performed. The payload is optional (i.e. can be `None`) or can contain any information necessary to perform the task.

This approach is used over multiple plugins.


### Command `watering_state` (sent to frontend)

The command `update_frontend_state` informs the frontend about the current watering state. For each actuator, it either says the watering is off or displays the zone that is currently watered and the remaining durations.

The backend will take care of constructing a string to display. The frontend will display the string. The message also consists of a duration per actuator which holds a valid value if the actuator is watering. The frontend can interpret this value as seconds and start at timer to count down and update the UI.


### Command `start_watering` (sent to backend)

Informs the backend that a new watering should be started. It's the backend's task to validate whether the data makes sense.

The payload is structured as follows:

```js
// payload layout:
{
    "zone": String,
    "duration": String
}
```

The `"duration"` string is formatted like `mm:ss` where `mm` resembles the minutes for which the watering should be active and `ss` the seconds. Only one zone can be activated per request.



## Available Actuators

### Six Way Sprinkler

This one is a rather complex actuator interface which controls one magnetic valve and up to six sprinklers. This is done by using one of those [Gardena Water Distributor](https://www.gardena.com/ca-en/products/watering/water-controls/water-distributor-automatic/966749301/) components. It has six output channels and only one of them is watered at a time. As the water pressure drops (by closing the magnetic valve), the water distributor will switch to the next channel.

The Six Way Sprinkler interface will keep track of the currently watered channel and water a channel only for a few seconds to skip it.

The zones from the `settings.json` file are used to assign the channels of the Water Distributor. The first given zone is assigned to channel `1`, the second zone to channel `2` and so on. The amount of given zones relates to the amount of channels that are activated in the Water Distributor.

*(Personal comment: I've been using Gardena's Water Distributor for multiple summers and it's really amazing. Works reliably and is way cheaper than buying and controlling six magnetic valves. When bought at another retailer, you can get the Water Distributor for a better price than on Gardena's website. I'm not sponsored by them or whatever, I just really like the product.)*


## Actuator Base Class

If you want to implement your own actuator this is the place to start. The actuator base class provides a bunch of methods that every actuator needs to implement and also some functionality to handle interruptable sleeping between controling the physical actuator. A simple example of this usecase can be found in the `SingleActuator` but all other actuators also use this system.