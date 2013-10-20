"""
PlexGDM.py - Version 0.2

__author__ = 'DHJ (hippojay) <plex@h-jay.com>'

This class implements the Plex GDM (G'Day Mate) protocol to discover
local Plex Media Servers.  Also allow client registration into all local
media servers.


This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.

Example usage
if __name__ == '__main__':
	client = plexgdm(debug=3)
	client.clientDetails("Test-Name", "Test Client", "3003", "Test-App", "1.2.3")
	client.start_all()
	while not client.discovery_complete:
		print "Waiting for results"
		time.sleep(1)
	time.sleep(20)
	print client.getServerList()
	if client.check_client_registration():
		print "Successfully registered"
	else:
		print "Unsuccessfully registered"
	client.stop_all()
"""
#===============================================================================
# IMPORT
#===============================================================================
import socket
import struct
import sys
import re
import threading
import time
import urllib2

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl

#===============================================================================
#
#===============================================================================
class plexgdm:

	#===========================================================================
	#
	#===========================================================================
	def __init__(self, debug=0):
		printl("", self , "S")

		self.discover_message = 'M-SEARCH * HTTP/1.0'
		self.client_header = '* HTTP/1.0'
		self.client_data = None
		self.client_id = None
		
		self._multicast_address = '239.0.0.250'
		self.discover_group = (self._multicast_address, 32414)
		self.client_register_group = (self._multicast_address, 32413)
		self.client_update_port = 32412

		self.server_list = []
		self.discovery_interval = 120
		
		self._discovery_is_running = False
		self._registration_is_running = False

		self.discovery_complete = False
		self.client_registered = False
		self.debug = debug

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def clientDetails(self, c_id, c_name, c_post, c_product, c_version):
		printl("", self , "S")

		self.client_data = "Content-Type: plex/media-player\nResource-Identifier: %s\nName: %s\nPort: %s\nProduct: %s\nVersion: %s" % ( c_id, c_name, c_post, c_product, c_version )
		self.client_id = c_id

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def getClientDetails(self):
		printl("", self , "S")

		if not self.client_data:
			printl("Client data has not been initialised.  Please use PlexGDM.clientDetails()", self, "D")

		printl("", self, "C")
		return self.client_data

	#===========================================================================
	#
	#===========================================================================
	def client_update (self):
		printl("", self , "S")

		update_sock = socket.socket(socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		
		#Set socket reuse, may not work on all OSs.
		try:
			update_sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		except:
			pass
		
		#Attempt to bind to the socket to recieve and send data.  If we can;t do this, then we cannot send registration
		try:
			update_sock.bind(('0.0.0.0',self.client_update_port))
		except:
			printl("Error: Unable to bind to port [%s] - client will not be registered" % self.client_update_port, self, "D")

			printl("", self, "C")
			return
		
		update_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
		update_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(self._multicast_address) + socket.inet_aton('0.0.0.0'))
		update_sock.setblocking(0)
		printl("Sending registration data: HELLO %s\n%s" % (self.client_header, self.client_data), self, "D")

		#Send initial client registration
		try:
			update_sock.sendto("HELLO %s\n%s" % (self.client_header, self.client_data), self.client_register_group)
		except:
			printl("Error: Unable to send registeration message", self, "D")

		#Now, listen for client discovery reguests and respond.
		while self._registration_is_running:
			try:
				data, addr = update_sock.recvfrom(1024)
				printl("Recieved UDP packet from [%s] containing [%s]" % (addr, data.strip()), self, "D")
			except socket.error:
				pass
			else:
				if "M-SEARCH * HTTP/1." in data:
					printl("Detected client discovery request from %s.  Replying" % addr, self, "D")
					try:
						update_sock.sendto("HTTP/1.0 200 OK\n%s" % self.client_data, addr)
					except:
						printl("Error: Unable to send client update message", self, "D")

					printl("Sending registration data: HTTP/1.0 200 OK\n%s" % self.client_data, self, "D")
					self.client_registered = True
			time.sleep(0.5)		

		printl("Client Update loop stopped", self, "D")

		#When we are finished, then send a final goodbye message to deregister cleanly.
		printl("Sending registration data: BYE %s\n%s" % (self.client_header, self.client_data), self, "D")
		try:
			update_sock.sendto("BYE %s\n%s" % (self.client_header, self.client_data), self.client_register_group)
		except:
			printl("Error: Unable to send client update message", self, "D")
					   
		self.client_registered = False

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def check_client_registration(self):
		printl("", self , "S")
		
		if self.client_registered and self.discovery_complete:
		
			if not self.server_list:
				printl("Server list is empty. Unable to check", self, "D")

				printl("", self, "C")
				return False

			try:
				media_server=self.server_list[0]['server']
				media_port=self.server_list[0]['port']

				printl("Checking server [%s] on port [%s]" % (media_server, media_port), self, "D")
				f = urllib2.urlopen('http://%s:%s/clients' % (media_server, media_port))
				client_result = f.read()
				if self.client_id in client_result:
					printl("Client registration successful", self, "D")
					printl("Client data is: %s" % client_result, self, "D")

					printl("", self, "C")
					return True
				else:
					printl("Client registration not found", self, "D")
					printl("Client data is: %s" % client_result, self, "D")

			except:
				printl("Unable to check status", self, "D")

		printl("", self, "C")
		return False

	#===========================================================================
	#
	#===========================================================================
	def getServerList (self):
		printl("", self , "S")

		printl("", self, "C")
		return self.server_list

	#===========================================================================
	#
	#===========================================================================
	def discover(self):
		printl("", self , "S")

		sock = socket.socket(socket.SOCK_DGRAM)

		# Set a timeout so the socket does not block indefinitely
		sock.settimeout(0.6)

		# Set the time-to-live for messages to 1 for local network
		ttl = struct.pack('b', 1)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

		returnData = []
		try:
			# Send data to the multicast group
			printl("Sending discovery messages: %s" % self.discover_message, self, "D")
			sock.sendto(self.discover_message, self.discover_group)

			# Look for responses from all recipients
			while True:
				try:
					data, server = sock.recvfrom(1024)
					printl("Received data from %s" % server, self, "D")
					printl("Data received is:\n %s" % data, self, "D")
					returnData.append( { 'from' : server,
										 'data' : data } )
				except socket.timeout:
					break
		finally:
			sock.close()

		self.discovery_complete = True

		discovered_servers = []

		if returnData:

			for response in returnData:
				update = { 'server' : response.get('from')[0] }

				#Check if we had a positive HTTP response
				if "200 OK" in response.get('data'):
			
					for each in response.get('data').split('\n'):

						update['discovery'] = "auto"
						update['owned']='1'
						update['master']= 1
						update['role']='master'
						update['class']=None
					
						if "Content-Type:" in each:
							update['content-type'] = each.split(':')[1].strip()
						elif "Resource-Identifier:" in each:
							update['uuid'] = each.split(':')[1].strip()
						elif "Name:" in each:
							update['serverName'] = each.split(':')[1].strip()
						elif "Port:" in each:
							update['port'] = each.split(':')[1].strip()
						elif "Updated-At:" in each:
							update['updated'] = each.split(':')[1].strip()
						elif "Version:" in each:
							update['version'] = each.split(':')[1].strip()
						elif "Server-Class:" in each:
							update['class'] = each.split(':')[1].strip()

				discovered_servers.append(update)					

		self.server_list = discovered_servers
		
		if not self.server_list:
			printl("No servers have been discovered", self, "D")
		else:
			printl("Number of servers Discovered: %s" % len(self.server_list), self, "D")
			for items in self.server_list:
				printl("Server Discovered: %s" % items['serverName'], self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def setInterval(self, interval):
		printl("", self , "S")

		self.discovery_interval = interval

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def stop_all(self):
		printl("", self , "S")

		self.stop_discovery()
		self.stop_registration()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def stop_discovery(self):
		printl("", self , "S")

		if self._discovery_is_running:
			printl("Discovery shutting down", self, "D")
			self._discovery_is_running = False
			self.discover_t.join()
			del self.discover_t
		else:
			printl("Discovery not running", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def stop_registration(self):
		printl("", self , "S")

		if self._registration_is_running:
			printl("Registration shutting down", self, "D")
			self._registration_is_running = False
			self.register_t.join()
			del self.register_t
		else:
			printl("Registration not running", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def run_discovery_loop(self):
		printl("", self , "S")

		#Run initial discovery
		self.discover()

		discovery_count=0
		while self._discovery_is_running:
			discovery_count+=1
			if discovery_count > self.discovery_interval:
				self.discover()
				discovery_count=0
			time.sleep(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def start_discovery(self, daemon = False):
		printl("", self , "S")

		if not self._discovery_is_running:
			printl("Discovery starting up", self, "D")
			self._discovery_is_running = True
			self.discover_t = threading.Thread(target=self.run_discovery_loop)
			self.discover_t.setDaemon(daemon)
			self.discover_t.start()
		else:
			printl("Discovery already running", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def start_registration(self, daemon = False):
		printl("", self , "S")

		if not self._registration_is_running:
			printl("Registration starting up", self, "D")
			self._registration_is_running = True
			self.register_t = threading.Thread(target=self.client_update)
			self.register_t.setDaemon(daemon)
			self.register_t.start()
		else:
			printl("Registration already running", self, "D")

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def start_all(self, daemon = False):
		printl("", self , "S")

		self.start_discovery(daemon)
		self.start_registration(daemon)

		printl("", self, "C")
