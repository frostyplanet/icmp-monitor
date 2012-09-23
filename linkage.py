#!/usr/bin/env python
# coding:utf-8

# author: frostyplanet@gmail.com

class Linkage (object):

    bitmap = None
    ip = None
    alarm_levels = None
    recover_thres = None
    last_state = None
    bad_count = 0
    recover_count = 0
    cur_alarm_level = 0
    total_latency = 0
    
    def __init__ (self, ip, alarm_levels, recover_thres):
        self.ip = ip
        assert isinstance (alarm_level, (tuple, list))
        assert recover_thres > 0
        self.alarm_levels = alarm_levels
        self.recover_thres = recover_thres
        self.reset_bitmap ()

    def reset_bitmap (self):    
        self.bitmap = []
        self.total_latency = 0

    def new_state (self, is_ok, latency):
        """ pass the current ping state, return alarm state , None for unchange, False for bad, True for normal """
        self.total_latency += latency
        bit = is_ok and '1' or '0'
        self.bitmap.append (bit)
        if is_ok:
            if self.last_state:
                self.bad_count = 0
                self.recover_count = 0
            else:
                self.bad_count += 1
                self.recover_count += 1
        else:
            self.bad_count += 1
            self.recover_count = 0

        if self.recover_count > 0 and self.recover_count == self.recover_thres:
            self.bad_count = 0
            self.last_state = True
            return self.last_state
        elif self.bad_count > 0 and self.alarm_levels:
            try:
                level = self.alarm_levels.index (self.bad_count)
                self.cur_alarm_level = level + 1
                self.last_state = False
                return self.last_state
            except ValueError:
                pass
        return None


    def stringify (self);
        state = self.last_state and "good" or "bad"
        avg_latency = -1
        if len (self.bitmap) > 0:
            avg_latency = self.total_latency / len (self.bitmap)
        return "%s :state %s, bitmap=%s, avg_rtt=%s" % (
                self.ip,
                state,
                "".join (self.bitmap),
                avg_latency
                )


        
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
