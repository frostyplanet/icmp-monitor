#!/usr/bin/env python
# coding:utf-8

# author: frostyplanet@gmail.com

import os
import sys
import config
from lib.log import Log
import lib.daemon as daemon
from lib.fping import fping
from mod.linkage import Linkage
from lib.job_queue import JobQueue
from mod.alarm import EmailAlarm, AlarmJob
import time
import signal


class ICMPMonitor (object):

    def __init__(self):
        self.is_running = False
        self.linkage_dict = dict()
        self.logger = Log("icmp_mon", config=config)
        self.alarm_q = JobQueue(self.logger)
        self.emailalarm = EmailAlarm(Log("alarm", config=config))
        self.logger_links = Log("links", config=config)
        if 'log_length_per_link' in dir(config):
            self.log_length_per_link = config.log_length_per_link
        else:
            self.log_length_per_link = 128
        if 'links' not in dir(config):
            self.logger.error("no 'links' in config")
            return
        g_alarm_levels = None
        g_recover = None
        if 'alarm_levels' in dir(config):
            g_alarm_levels = self._parse_alarm_levels(config.alarm_levels)
        if 'recover' in dir(config):
            g_recover = int(config.recover)
        links = config.links
        if isinstance(links, dict):
            for ip, v in links.iteritems():
                if not isinstance(v, dict):
                    v = dict()
                ttl = v.get('ttl')
                if ttl >= 0:
                    pass
                else:
                    ttl = 0
                alarm_levels = v.get('alarm_levels')
                if not alarm_levels and g_alarm_levels:
                    alarm_levels = g_alarm_levels
                elif alarm_levels:
                    alarm_levels = self._parse_alarm_levels(alarm_levels)
                    if not alarm_levels:
                        continue
                else:
                    self.logger.error(
                        "config: %s, missing alarm_levels value" % (ip))
                    continue
                recover = v.get('recover')
                if recover:
                    recover = int(recover)
                elif not recover and g_recover:
                    recover = g_recover
                else:
                    self.logger.error(
                        "config: %s, missing recover value" % (ip))
                    continue
                self.linkage_dict[ip] = Linkage(ip, alarm_levels, recover)
        self.logger.info("%d link loaded from config" %
                         (len(self.linkage_dict.keys())))

    def _parse_alarm_levels(self, alarm_levels, ip=""):
        if not isinstance(alarm_levels, (tuple, list)):
            self.logger.error("config: %s, alarm_levels is not a list" % (ip))
            return
        _alarm_levels = filter(lambda x: isinstance(x, int), alarm_levels)
        if len(_alarm_levels) != len(alarm_levels):
            self.logger.error(
                "config: %s, elements in alarm_levels must be integers" % (ip))
            return
        return _alarm_levels

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.alarm_q.start_worker(1)
        self.logger.info("started")

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self.alarm_q.stop()
        self.logger.info("stopped")

    def _alarm_enqueue(self, link):
        t = "%Y-%m-%d %H:%M:%S"
        ts = "[%s]" % (time.strftime(t, time.localtime()))
        job = AlarmJob(
            self.emailalarm, ts + link.alarm_text(), link.details())
        self.alarm_q.put_job(job)

    def loop(self):
        ips = self.linkage_dict.keys()
        while self.is_running:
            start_time = time.time()
            recv_dict, error_dict = fping(ips, 1)
            for ip, rtt in recv_dict.iteritems():
                link = self.linkage_dict[ip]
                res = link.new_state(True, rtt)
                if res:
                    self._alarm_enqueue(link)
                print ip, "ok", rtt
                if len(link.bitmap) == self.log_length_per_link:
                    self.logger_links.info(link.details())
                    link.reset_bitmap()
            for ip, err in error_dict.iteritems():
                link = self.linkage_dict[ip]
                res = link.new_state(False, 0)
                if res is False:
                    self._alarm_enqueue(link)
                print ip, "err", link.bitmap
                if len(link.bitmap) == self.log_length_per_link:
                    self.logger_links.info(link.details())
                    link.reset_bitmap()

            end_time = time.time()
            if end_time < start_time + 1:
                time.sleep(1 - end_time + start_time)


stop_signal_flag = False


def _main():
    prog = ICMPMonitor()

    def exit_sig_handler(sig_num, frm):
        global stop_signal_flag
        if stop_signal_flag:
            return
        stop_signal_flag = True
        prog.stop()
        return
    prog.start()
    signal.signal(signal.SIGTERM, exit_sig_handler)
    signal.signal(signal.SIGINT, exit_sig_handler)
    prog.loop()
    return


def usage():
    print "usage:\t%s star/stop/restart\t#manage forked daemon" % (sys.argv[0])
    print "\t%s run\t\t# run without daemon, for test purpose" % (sys.argv[0])
    os._exit(1)


if __name__ == "__main__":

    logger = Log("daemon", config=config)
                  # to ensure log is permitted to write
    pid_file = "icmp_mon.pid"
    mon_pid_file = "icmp_mon_mon.pid"

    if len(sys.argv) <= 1:
        usage()
    else:
        action = sys.argv[1]
        daemon.cmd_wrapper(action, _main, usage, logger,
                           config.log_dir, "/tmp", pid_file, mon_pid_file)


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
