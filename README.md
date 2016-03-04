icmp-monitor
============

Monitor network using icmp.

Single thread parallel ping, with custom alarm level for each ip.
Use SMTP to send alarm mail.
Supports monitor target specified by hostname or IP.
The ping interval is 1 second.
Must be run with the root user.

Configuration example
---------------------
Refer to config.py

Log files
----------
icmp_mon.log    # start / stop message

alarm.log       #link up/down alarm

link.log        # regular log for monitor target, with rtt average


	xxx.foobar.com :good, bitmap=1111111111111111111101111111111, avg_rtt=1.43ms
	
	The above log explain:  in the bitmap "1" for normal, "0" for packet loss
