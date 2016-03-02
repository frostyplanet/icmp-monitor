#!/usr/bin/env python
# coding:utf-8

import _env
from mod.alarm import EmailAlarm
from mod.linkage import Linkage
from lib.log import Log
import config


def test_alarm_bad():
    alarm = EmailAlarm(Log("test", config=config))
    link = Linkage("1.1.1.1", [1, 10], 5)
    link.last_state = False
    link.bitmap = ["1", "1", "0"]
    link.cur_alarm_level = 1
    alarm.send(link.alarm_text(), link.details())


def test_alarm_good():
    alarm = EmailAlarm(Log("test", config=config))
    link = Linkage("1.1.1.1", [1, 10], 5)
    link.last_state = True
    link.bitmap = ["1", "1", "1", "1", "1"]
    link.cur_alarm_level = 1
    alarm.send(link.alarm_text(), link.details())


if __name__ == '__main__':
    test_alarm_good()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
