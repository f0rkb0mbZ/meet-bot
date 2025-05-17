#!/bin/bash

pulseaudio --daemonize=yes --disallow-exit=true
pactl load-module module-null-sink sink_name=virtual_sink sink_properties=device.description="VirtualSink"
pactl set-default-sink virtual_sink
pactl load-module module-remap-source source_name=virtual_source master=virtual_sink.monitor source_properties=device.description="VirtualSource"
pactl set-default-source virtual_source

