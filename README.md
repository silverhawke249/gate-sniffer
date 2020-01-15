# gate-sniffer

A collection of scripts to examine raw data streamed to Spiral Knights, for arcade gate viewing purposes.

The functions of each script will be detailed below.

[TOC]

#### convert_gates.py

Self-explanatory. Converts the most recent dump (see [fetch_data.py](#fetch_data.py "fetch_data.py")) into a format appropriate for use with gatemap-viewer, which is stored in `/output/`.

#### fetch_data.py

Listens to network traffic and saves a particular stream to disk, which is stored in `/raw_dump/`.

#### gates_info.py

Prints data on the gates available in the most recent dump to stdout. Currently displays gate ID, gate name, foreground and background color, and strata themes.

#### get_gates.py

Reads the most recent dump and saves data for each gate as its own file, for easier examination. Data will be saved to `./gate[X].dat`, where `[X]` is a number from 0.

#### toolkit.py

Contains all the functions needed to read and handle the gate data.

#### gatemap.bt

Template file used to parse bin
ary gate data.