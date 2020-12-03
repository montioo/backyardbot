# timetable Plugin for Byb

More of a test plugin as of now. Demonstrates the folder structure and shows which classes one needs to subclass to create a plugin.

Since the plugin manager doesn't exist yet, the plugins have to be imported manually in `main.py`.


## Websocket Client <-> Plugin Communication

The framework enables a communication from websocket client to plugin. The plugin internally wraps all sent messages in a message class that allows the server to direct the message to the correct plugin or websocket client.

This procedure only makes sure that messages arrive at the correct entities and the plugin implementation itself doesn't have to deal with this.

```
              websocket   +--------+   topics
 frontend  ---------------+ Server +------------  backend
                          +--------+
```

The frontend refers to the part of the plugin implementation that runs in a user's browser, i.e. the js scripts. The backend is the python implementation of the plugin. One backend can be connected to multiple frontends, i.e. one for every user.

However, the plugin will also want to establish a system where different message types are available for different tasks. `command` refers to the handler that should be used by the receiver (frontend or backend) to process the data that is accessed with the `payload` key.

All messages need to follow a certain structure, regardless of whether they are sent from the frontend to the backend or vice versa.

```js
{
    "command": String,
    "payload": Object
}
```

The TimeTable plugin knows the following messages:

### Messages from backend to frontend:

`command` | `payload` | note
---|---|---
`timetable_contents` | list of timetable entries | Each entry in the timetable is represented as a dict of defining properties, like the scheduled time, the channels to use and so on. The table will be displayed in the order in which it was transferred.


### Messages from frontend to backend:

`command` | `payload` | note
---|---|---
`add_entries` | list of dicts with entries | Entries are "broken up" so that each entry only holds one day. But an entry can still hold multiple zones.
`remove_entry` | database entry id | The database automatically assigns an ID to each element that it holds. The element can be identified by this ID and then be deleted from the DB.


## Timetable Database Structure:

Each entry of the timetable database has the following structure:

```js
{
    "time_hh": int,
    "time_mm": int,
    "weekday": int,
    "zones": [int],
    "duration": int
}
```

It is served to the database as a dict and the database will assign an `id` to each object in the database. This id is also used by the frontend implementation to identify entries that should be deleted.

The structure of a new entry for the database is built by the frontend implementation in js, sent over to the server using a websocket and from there it is forwarded over a topic to the plugin's backend implementation. The server takes care of parsing the json string that was sent by the frontend and the backend simply has to store the new entry in the database, without any additional modification to the data.

In the same way, the backend only needs to read data from the table and send it to the frontend(s) to have it displayed there.
