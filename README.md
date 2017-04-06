# README #
this is for Alexa skill POC and allow Talisman to upload some CAN data
Last mod : I Ravelo, on 06apr2017

CarListener is a python application for retrieving and parsing data from a car CAN bus using an [OpenXC](http://openxcplatform.com/) compatible dongle. 
It is designed to be run on a Bluetooth enabled Raspberry PI.

The application is meant to be coupled with a dongle running a custom
OpenXC firmware and library, implementing the `filter_message()` command, but
it can also be used with a standard OpenXC one by simply disabling the 
`FilterConfigurator` class. The custom firmware can be provided upon request.

The Raspberry PI can run on the standard [Raspbian](https://www.raspberrypi.org/downloads/raspbian/) distro, an image of a
preconfigured Raspbian SD will be provided upon request.

### Why do I need CarListener? Can't I simply use OpenXC? ###

CarListener was born to add more flexibility to the OpenXC project:

- You don't need to recompile a new OpenXC firmware any time you need to get 
  a different set of messages from the CAN bus
- You can reconfigure the information to read/write from/to the CAN bus by
  simply editing a couple of JSON files
- You can  "consume" your data in many different ways (send them to the 
  cloud, write them over a file, ...).
  You can also easily write your  custom "data consumer" and add it to the 
  application- You can add more information to the data you retrieve (e.g., 
  GPS position)

### The architecture ###

CarListener is built around a single class named `EventManager`. Every event 
like the reception of a new CAN message, the new GPS position, the connection
to the dongle and so on, is fired directly on the `EventManager`, which will
asynchronously notify it to all the "data consumers" that were registered to it. Here is a simple schematic:


```
#!

+------+    +------+
|  VI  |===>| MAIN | VI_EVENT
| DONG | |  | PROG |============|               +------+
+------+ |  +------+            |               | MQTT |
         |                      |            |=>| CONS |===>[CLOUD]
         |  +------+            |            |  +------+
         |=>| CAN  | CAN_EVENT  |            |  
         |  | PRSR |==========| |  +-------+ |
         |  +------+          | |=>|       | |  +------+
         |                    ====>| EVENT |===>| PRNT |
         |  +------+          ====>| MANGR | |  | CONS |===>[TERMINAL]
         |=>| OBD  | OBD_EVENT| |=>|       | |  +------+
            | PRSR |==========| |  +-------+ |
            +------+            |            |
                                |            |  +------+
+------+    +------+            |            |=>| FILE |
| GPS  |===>| GPS  | GPS_EVENT  |               | CONS |==>[FILE]
| SHLD |    | PRSR |============|               +------+
+------+    +------+

```

### TODO Deployment ###

Actually, a Raspbian image is provided with all dependencies preinstalled.  
In the future, a guide on how to prepare the Raspbian image will be provided.
All the python libraries required for executing CarListener are going to be moved
into the application itself in order to minimize external dependencies and 
versions problems.
Having all the python stuff in one place will also simplify the deployment in
minimalistic environments like the [piCore](http://forum.tinycorelinux.net/index.php/board,57.0.html) Linux distribution.

### Running CarListener ###

CarListener can be run directly from a terminal by entering the main 
application and executing:


```
#!

./carlistener.py
```


The application is meant to be run forever but you can interrupt it by pressing `ctrl+c` (it may take some time to stop)

### Author ###
Dario Fiumicello - <dario.fiumicello@gmail.com>
