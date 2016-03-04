#!/usr/bin/env python
# coding:utf-8

import os
from os.path import dirname

base_dir = dirname(__file__)
# for log.py
log_dir = os.path.join(base_dir, "log")
log_rotate_size = 20000
log_backup_count = 10
log_level = "DEBUG"
# for log.py

log_length_per_link = 60       # Link state will be put into 60 size bitmap, 1 for up, 0 for down
alarm_levels = [10, 60, 600]   # Send level 1/2/3 alarm after 10/60/600 seconds down time
recover = 20   # Recover after 20 seconds no packet loss
links = {
    "127.0.0.1": None,  # Use default settings
    "192.168.1.1": {    # Override default settings
        "alarm_levels": [10, 60, 600],
        "recover": 20,
    },
}


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
