#!/usr/bin/env python
# coding:utf-8

import os
from os.path import dirname

base_dir = dirname (__file__)
# for log.py
log_dir = os.path.join (base_dir, "log")
log_rotate_size = 20000
log_backup_count = 10
log_level = "DEBUG"
# for log.py

log_length_per_link = 60
links = {
        "127.0.0.1": {
            "ttl": 0, # no limit
            "alarm_levels": [10, 60, 600],
            "recover": 20,
            },
        "192.168.1.1": {
            "ttl": 0, # no limit
            "alarm_levels": [10, 60, 600],
            "recover": 20,
            }, 
        }



# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
