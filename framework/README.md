# framework Documentation

This folder holds the components of the framework that enables building a plugin based application like backyardbot.

It is developed together with backyardbot but aims to be a generic framework that can be utilized for other systems as well.


## Plugin System

TODO



### Plugin loop

A plugin might want to do some recurring computation, e.g. read a sensor.

One option to make this happen is to have some kind of `self.spin()` at the end of the plugin's init method. Like with ROS nodes the plugin either calls this to do nothing else or it can set up a loop to compute stuff.

All of this should be written with asyncio.