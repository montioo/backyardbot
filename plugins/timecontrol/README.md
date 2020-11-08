# time control plugin for Byb

Tasks of this plugin:

- read database of time table entries
- calculate the next occurrence of each entry
- trigger an entry as soon as necessary


## Data structures

- Time table entry, look at timetable plugin.
- Task format. Which has to be interpretable by the actuator plugin.



## How to deal with sensors?

A sensor's reading could influence the watering duration.
Maybe have a list of "modifiers" that act on sensor readings. But that's a problem for later.
