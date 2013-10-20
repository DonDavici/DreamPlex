# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

Some of the code is from other plugins:
all credits to the coders :-)

DreamPlex Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

DreamPlex Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
"""
#===============================================================================
# IMPORT
#===============================================================================
import socket
import struct

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
#===============================================================================
# 
#===============================================================================
def wake_on_lan(macaddress):
	printl ("", "DPH_WOL::wake_on_lan", "S")
	printl ("using this mac ... " + macaddress, "DPH_WOL::wake_on_lan", "i")
	
	# Check macaddress format and try to compensate.
	if len(macaddress) == 12:
		pass
	elif len(macaddress) == 12 + 5:
		sep = macaddress[2]
		macaddress = macaddress.replace(sep, '')
	else:
		printl ("Incorrect MAC address format", "DPH_WOL::wake_on_lan", "W")
		raise ValueError('Incorrect MAC address format')

	# Pad the synchronization stream.
	data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
	send_data = '' 

	# Split up the hex values and pack.
	for i in range(0, len(data), 2):
		send_data = ''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

	# Broadcast it to the LAN.
	sock = socket.socket(socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	sock.sendto(send_data, ('<broadcast>', 7))
	
	printl ("", "DPH_WOL::wake_on_lan", "C")