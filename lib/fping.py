#!/usr/bin/env python

"""
    A pure python ping implementation using raw socket.

    Note that ICMP messages can only be sent from processes running as root.

    Derived from ping.c distributed in Linux's netkit. That code is
    copyright (c) 1989 by The Regents of the University of California.
    That code is in turn derived from code written by Mike Muuss of the
    US Army Ballistic Research Laboratory in December, 1983 and
    placed in the public domain. They have my thanks.

    Bugs are naturally mine. I'd be glad to hear about them. There are
    certainly word - size dependenceies here.

    Copyright (c) Matthew Dixon Cowles, .
    Distributable under the terms of the GNU General Public License
    version 2. Provided with no warranties of any sort.

    Original Version from Matthew Dixon Cowles:
      -> ftp://ftp.visi.com/users/mdc/ping.py

    Rewrite by Jens Diemer:
      -> http://www.python-forum.de/post-69122.html#69122

    Rewrite by George Notaras:
      -> http://www.g-loaded.eu/2009/10/30/python-ping/

    Rewrite by Neptune Ning <frostyplanet@gmail.com> <an.ning@aliyun-inc.com> 2011.7.15
        add parallel ping multiple address feature (only tested on linux), simular to fping.
        not supporting count parameter yet.
        
        Fix rtt time resolution 2016.3.21

    Revision history
    ~~~~~~~~~~~~~~~~

    November 8, 2009
    ----------------
    Improved compatibility with GNU/Linux systems.

    Fixes by:
     * George Notaras -- http://www.g-loaded.eu
    Reported by:
     * Chris Hallman -- http://cdhallman.blogspot.com

    Changes in this release:
     - Re-use time.time() instead of time.clock(). The 2007 implementation
       worked only under Microsoft Windows. Failed on GNU/Linux.
       time.clock() behaves differently under the two OSes[1].

    [1] http://docs.python.org/library/time.html#time.clock

    May 30, 2007
    ------------
    little rewrite by Jens Diemer:
     -  change socket asterisk import to a normal import
     -  replace time.time() with time.clock()
     -  delete "return None" (or change to "return" only)
     -  in checksum() rename "str" to "source_string"

    November 22, 1997
    -----------------
    Initial hack. Doesn't do much, but rather than try to guess
    what features I (or others) will want in the future, I've only
    put in what I need now.

    December 16, 1997
    -----------------
    For some reason, the checksum bytes are in the wrong order when
    this is run under Solaris 2.X for SPARC but it works right under
    Linux x86. Since I don't know just what's wrong, I'll swap the
    bytes always and then do an htons().

    December 4, 2000
    ----------------
    Changed the struct.pack() calls to pack the checksum and ID as
    unsigned. My thanks to Jerome Poincheval for the fix.



    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate: $
    $Rev: $
    $Author: $
"""

import os
import sys
import socket
import struct
import select
import time
import errno

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8  # Seems to be the same on Solaris.

TIME_DATA_FORMAT = "dd"
TIME_DATA_LEN = struct.calcsize(TIME_DATA_FORMAT)

def checksum(source_string):
    """
    I'm not too confident that this is right but testing seems
    to suggest that it gives the same answers as in_cksum in ping.c
    """
    _sum = 0
    strlen = len(source_string)
    count = 0
    while strlen > 1:
        _sum += ord(source_string[count]) + (
            ord(source_string[count + 1]) << 8)
        strlen -= 2
        count += 2
    if strlen == 1:
        _sum += ord(source_string[count])
    _sum = (_sum >> 16) + (_sum & 0xffff)
    _sum += (_sum >> 16)
    answer = ~_sum
    answer = answer & 0xffff

# Swap bytes. Bugger me if I know why.
#    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(sock, ID):
    """
    receive the ping  (ip, rtt) from the socket. rtt is float value in seconds
    """
    recv_packet, addr = sock.recvfrom(1024)
    icmp_header = recv_packet[20:28]
    icmptype, code, _checksum, packet_id, sequence = struct.unpack(
        "bbHHh", icmp_header
    )
    if icmptype == 0 and packet_id == ID:
        time_sent1, time_sent2 = struct.unpack(
            TIME_DATA_FORMAT, recv_packet[28:28 + TIME_DATA_LEN])
        time_sent = time_sent1 + time_sent2 / 1000.0 / 1000.0
        return (addr[0], time.time() - time_sent)
    else:
        raise socket.error(errno.EAGAIN, "EAGAIN")


def send_one_ping(my_socket, dest_addr, ID):
    """
    Send one ping to the given >dest_addr<, return the timestamp when sent
    """

    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    time_size = struct.calcsize("dd")
    data = (192 - time_size) * "Q"
    timestamp = time.time()
    z = int(timestamp)
    data = struct.pack("dd", z, int(1000 * 1000 * (timestamp - z))) + data

    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1))  # Don't know about the 1
    return timestamp

class FPing(object):

    def __init__(self, dest_addrs):
        assert isinstance(dest_addrs, list)
        self.dest_addrs = dest_addrs
        icmp = socket.getprotobyname("icmp")
        self.my_ID = os.getpid() & 0xFFFF
        self.ip_host_dict = dict()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
            self.sock.setblocking(0)
        except socket.error, (err, msg):
            if err == 1:
                # Operation not permitted
                msg = msg + (
                    " - Note that ICMP messages can only be sent from processes"
                    " running as root."
                )
                raise socket.error(msg)
            raise  # raise the original error

    def ping(self, timeout):
        """
        returns (recv_dict, error_dict)
        there's rt in recv_dict, and error reason in error_dict.
        dest_addrs only accept ip addresses.
        """
        send_dict = dict()
        recv_dict = dict()
        error_dict = dict()
        for dest_addr in self.dest_addrs:
            try:
                dest_ip = socket.gethostbyname(dest_addr)
                if dest_ip != dest_addr:
                    self.ip_host_dict[dest_ip] = dest_addr
                    self.ip_host_dict[dest_addr] = dest_ip
            except (socket.gaierror, socket.herror, socket.error), e:
                error_dict[dest_addr] = e

        for dest_addr in self.dest_addrs:
            try:
                if error_dict.has_key(dest_addr):
                    continue
                dest_ip = self.ip_host_dict.get(dest_addr)
                if not dest_ip:
                    dest_ip = dest_addr
                send_one_ping(self.sock, dest_ip, self.my_ID)
                send_dict[dest_addr] = 1
            except (socket.gaierror, socket.herror, socket.error), e:
                error_dict[dest_addr] = e

        time_left = timeout
        time1 = time.time()
        sock_list = [self.sock]
        while True:
            try:
                time_left = float(timeout - time.time() + time1)
                if time_left <= 0.0:
                    break
                while send_dict:
                    (ip, rrt) = receive_one_ping(self.sock, self.my_ID)
                    if not send_dict.has_key(ip):
                        host = self.ip_host_dict.get(ip)
                        if not host:
                            continue
                        recv_dict[host] = rrt
                        del send_dict[host]
                    else:
                        recv_dict[ip] = rrt
                        del send_dict[ip]
                if not send_dict:
                    break
            except select.error, e:
                if e[0] == errno.EINTR:
                    continue
                raise e
            except socket.error, e:
                if e[0] in [errno.EINTR, errno.EAGAIN]:
                    select.select(sock_list, [], [], time_left)
                    time_left = timeout - time.time() + time1
                    continue
                raise e

        for addr in send_dict.iterkeys():
            error_dict[addr] = "timeout"
        return (recv_dict, error_dict)


def verbose_ping(dest_addrs, timeout=2):
    """
    Send >count< ping to >dest_addr< with the given >timeout< and display
    the result.
    """
    assert isinstance(dest_addrs, list)
    recv_dict = err_dict = None
    try:
        o = FPing(dest_addrs)
        (recv_dict, err_dict) = o.ping(timeout)
    except socket.gaierror, e:
        print "failed. (socket error: '%s')" % e[1]
        return
    for recv_addr, rrt in recv_dict.iteritems():
        print "ok", recv_addr, rrt * 1000, "ms"
    for err_addr, e in err_dict.iteritems():
        print "err", err_addr, str(e)


def usage():
    print """ %s -W timeout [IP] """ % (sys.argv[0])


def main():
    import getopt
    optlist = None
    args = None
    try:
        optlist, args = getopt.gnu_getopt(sys.argv[1:], "W:h", ["help"])
    except getopt.GetoptError, e:
        print >> sys.stderr, str(e)
        sys.exit(1)
    if len(args) == 0:
        print >> sys.stderr, "target ip is required"
        sys.exit(1)
    timeout = 2
    for opt, v in optlist:
        if opt in ['-h', '--help']:
            usage()
            sys.exit(0)
        elif opt == '-W':
            timeout = float(v)
    print "timeout", timeout
    verbose_ping(args, timeout=timeout)

if __name__ == '__main__':
    main()


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
