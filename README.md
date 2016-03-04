icmp-monitor
============

Monitor network using icmp.

Single thread parallel ping, with custom alarm level for each ip.
Use SMTP to send alarm mail.
Supports monitor target specified by hostname or IP.

Configuration example
---------------------
Refer to config.py

Log files
----------
icmp_mon.log    # start / stop message

alarm.log       #link up/down alarm

link.log        # regular log for monitor target, with rtt average

