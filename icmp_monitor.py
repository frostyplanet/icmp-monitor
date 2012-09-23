#!/usr/bin/env python
# coding:utf-8

# author: frostyplanet@gmail.com

import os
import sys
import config
from lib.log import Log
import lib.daemon as daemon
from lib.fping import fping
from linkage import Linkage
import time
import signal

class ICMPMonitor (object):
    
    def __init__ (self):
        self.is_running = False
        self.linkage_dict = dict ()
        self.logger = Log ("icmp_mon", config=config) 
        self.logger_links = Log ("links", config=config)
        if 'log_length_per_link' in dir (config):
            self.log_length_per_link = config.log_length_per_link
        else:
            self.log_length_per_link = 128
        if 'links' not in dir (config):
            self.logger.error ("no 'links' in config")
            return
        links = config.links
        if isinstance (links, dict):
            for ip, v in links.iteritems ():
                alarm_levels = None
                ttl = None
                recover = None
                try:
                    alarm_levels = v['alarm_levels']
                    ttl = v['ttl']
                    recover = v['recover']
                except KeyError, e:
                    self.logger.error ("config: ip %s, %s" % (ip, str(e)))
                    continue
                if ttl < 0:
                    self.logger.error ("config: ip %s, ttl < 0" % (ip))
                    continue
                if not isinstance (alarm_levels, (tuple, list)):
                    self.logger.error ("config: ip %s, alarm_levels is not a list" % (ip))
                    continue
                _alarm_levels = filter (lambda x: isinstance (x, int), alarm_levels) 
                if len (_alarm_levels) != len (alarm_levels):
                    self.logger.error ("config: ip %s, elements in alarm_levels must be integers")
                    continue
                if not isinstance (recover, int):
                    self.logger.error ("config: ip %s, recover is not integer")
                    continue
                self.linkage_dict[ip] = Linkage (ip, alarm_levels, recover)
        self.logger.info ("%d link loaded from config" % (len (self.linkage_dict.keys ())))

    def start (self):
        self.is_running = True

    def stop (self):
        self.is_running = False

    def loop (self):
        ips = self.linkage_dict.keys ()
        while self.is_running:
            start_time = time.time ()
            recv_dict, error_dict = fping (ips, 1)
            for ip, rtt in recv_dict.iteritems ():
                link = self.linkage_dict[ip]
                res = link.new_state (True, rtt)
                if res is True:
                    pass
                    # recover
                if len (link.bitmap) == self.log_length_per_link:
                    self.logger_links.info (link.stringify ())
                    link.reset_bitmap ()
            for ip, err in error_dict.iteritems ():
                link = self.linkage_dict[ip]
                res = link.new_state (False, 0)
                if res is False:
                    pass
                    # bad
                if len (link.bitmap) == self.log_length_per_link:
                    self.logger_links.info (link.stringify ())
                    link.reset_bitmap ()
                
            end_time = time.time ()
            if end_time < start_time + 1:
                time.sleep (1 - end_time - start_time)

            
stop_signal_flag = False

def _main():
    prog = ICMPMonitor ()

    def exit_sig_handler (sig_num, frm):
        global stop_signal_flag
        if stop_signal_flag:
            return
        stop_signal_flag = True
        prog.stop ()
        return
    prog.start ()
    signal.signal (signal.SIGTERM, exit_sig_handler)
    signal.signal (signal.SIGINT, exit_sig_handler)
    prog.loop ()
    return

def usage ():
    print "usage:\t%s star/stop/restart\t#manage forked daemon" % (sys.argv[0])
    print "\t%s run\t\t# run without daemon, for test purpose" % (sys.argv[0])
    os._exit (1)


if __name__ == "__main__":

    logger = Log ("daemon", config=config) # to ensure log is permitted to write
    pid_file = "icmp_mon.pid"
    mon_pid_file = "icmp_mon_mon.pid"

    if len (sys.argv) <= 1:
        usage ()
    else:
        action = sys.argv[1]
        daemon.cmd_wrapper (action, _main, usage, logger, config.log_dir, "/tmp", pid_file, mon_pid_file)



# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
