# Time Control Plugin for backyardbot

Tasks of this plugin:

- Read database of timetable entries
- Calculate the next occurrence of each entry
- Trigger an entry as soon as necessary

This is the behavior in the automatic mode. If the automatic mode is disabled, the plugin won't do anything.

## Communication between Backend and Frontend

All messages need to follow a certain structure, regardless of whether they are sent from the frontend to the backend or vice versa.

```js
{
    "command": String,
    "payload": Object
}
```

The receiver uses the command field to determine what kind of action should be performed. The payload is optional (i.e. can be `None`) or can contain any information necessary to perform the task.

### Command `plugin_state` (sent to frontend)

The command `plugin_state` advises the frontend to exchange the information it currently displays with the new ones that are contained in the payload.

```js
// payload layout:
{
    "auto_state": Boolean,
    "next_time_day": String,
    "next_zone_duration": String
}
```

`auto_state` signals whether the automatic mode is activated, which will read data from the timetable database and start waterings based on this data. `next_time_day` is a string which contains the next time and (week)day a watering will happen. `next_zone_duration` is also a string and gives information about the next zone that will be watered and the duration of the watering.

### Command `skip_next_watering` (sent to backend)

The command `skip_next_watering` has an empty payload field and advises the server to skip the next element in the watering schedule. The server will calculate the next occurrence of the rescheduled object, resort the list of scheduled waterings and respond to all frontends with the updated automatic mode description.

### Command `toggle_auto_mode` (sent to backend)

The command `toggle_auto_mode` has a bool value as its payload which indicates the requested state of the automatic watering mode. Deactivating the automatic watering is always possible, activating it is only possible if there is at least one entry in the timetable database. The server will reply with an updated status for all frontends to display.


## Data structures

- Time table entry, look at timetable plugin.
- Task format. Which has to be interpretable by the actuator plugin. TODO



## How to deal with sensors?

A sensor's reading could influence the watering duration.
Maybe have a list of "modifiers" that act on sensor readings. But that's a problem for later.
