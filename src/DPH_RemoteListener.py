# -*- coding: utf-8 -*-
"""
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

Based on XBMCLocalProxy 0.1 Copyright 2011 Torben Gerkensmeyer
Based on PleXBMC Remote Helper 0.2 Copyright 2013 Hippojay

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
import threading
import BaseHTTPServer
import inspect
import traceback
import re
import time

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler, test
from thread import start_new_thread
from threading import Thread

from Plugins.Extensions.DreamPlex.__init__ import getVersion
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, getBoxInformation
from Plugins.Extensions.DreamPlex.DPH_PlexGdm import plexgdm

#===============================================================================
#
#===============================================================================
class HttpDeamon():

	#===========================================================================
	#
	#===========================================================================
	def __init__(self):
		pass

	#===========================================================================
	#
	#===========================================================================
	def startDeamon(self):
		printl("", self, "S")

		t = Thread(target=runHttp)
		t.start()
		
		client = plexgdm(debug=3)
		version = str(getVersion())
		gBoxType = getBoxInformation()
		clientBox = "8000"
		printl("clientBox: " + str(gBoxType), self, "D")
		client.clientDetails(clientBox, "192.168.45.80", "8000", "DreamPlex", version)
		client.start_registration()
		
		if client.check_client_registration():
			printl("Successfully registered", self, "D")
		else:
			printl("Unsuccessfully registered", self, "D")

		printl("", self, "C")

class MyHandler(BaseHTTPRequestHandler):
	"""
	Serves a HEAD request
	"""

	#===========================================================================
	#
	#===========================================================================
	def do_HEAD(self, s):
		printl("", self, "S")

		printl("Serving HEAD request...", self, "D")
		s.answer_request(0)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def do_GET(self, s):
		printl("", self, "S")

		printl("Serving GET request...", self, "D")
		s.answer_request(1)

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def answer_request(self, s):
		printl("", self, "S")

		try:
			#s.send_response(200)
			request_path=s.path[1:]
			request_path=re.sub(r"\?.*","",request_path)
			printl("request path is: [%s]" % request_path, self, "D")

			if request_path=="version":
				#s.end_headers()
				s.wfile.write("DreamPlex Helper Remote Redirector: Running\r\n")
				s.wfile.write("Version: 0.1")
				s.send_response(200)

			elif request_path=="verify":
				printl("DreamPlex Helper -> listener -> detected remote verification request", self, "D")
				#command=XBMCjson("ping()")
				#result=command.send()
				s.wfile.write("XBMC JSON connection test:\r\n")
				s.wfile.write(result)
				s.send_response(200)

			elif request_path == "xbmcCmds/xbmcHttp":
				s.wfile.write("<html><li>OK</html>")
				s.send_response(200)
				printl("DreamPlex Helper -> listener -> Detected remote application request", self, "D")
				printl("Path: %s" % s.path, self, "D")
				command_path=s.path.split('?')[1]

				printl("Request: %s " % urllib.unquote(command_path), self, "D")

				if command_path.split('=')[0] == 'command':
					printl("Command: Sending a json to Plex", self, "D")
					#command=XBMCjson(urllib.unquote(command_path.split('=',1)[1]))
					#command.send()
			else:
				s.send_response(200)
		except:
				traceback.print_exc()
				s.wfile.close()

				printl("", self, "C")
				return
		try:
			s.wfile.close()
		except:
			pass

		printl("", self, "C")
	#===========================================================================
	#
	#===========================================================================
	def address_string(self):
		printl("", self, "S")

		host, port = self.client_address[:2]
		#return socket.getfqdn(host)

		printl("", self, "C")
		return host 

#===========================================================================
#
#===========================================================================
def runHttp(HandlerClass = MyHandler,ServerClass = HTTPServer, protocol="HTTP/1.0"):
		"""
		Test the HTTP request handler class.
	
		This runs an HTTP server on port 8000 (or the first command line
		argument).
		"""
		printl("", self, "S")

		port = 8000
		server_address = ('', port)
	
		HandlerClass.protocol_version = protocol
		httpd = ServerClass(server_address, HandlerClass)
	
		sa = httpd.socket.getsockname()
		printl("Serving HTTP on" + sa[0] + "port " + sa[1] + "...", self, "D")
		httpd.serve_forever()

		printl("", self, "C")