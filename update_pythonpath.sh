#!/bin/bash

# Add this folder to python path to make the modules importable
# TODO: Enable plugins to import from their own folder in PluginManager
export PYTHONPATH=`pwd`:`pwd`/plugins/timecontrol

# enable asyncio debug mode
export PYTHONASYNCIODEBUG=1