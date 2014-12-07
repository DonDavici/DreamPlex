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
import re
import traceback

from time import sleep
from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler

from Components.config import config

from DPH_Singleton import Singleton
from DP_PlexLibrary import PlexLibrary
from DPH_SubscriptionManager import SubscriptionManager

from __common__ import printl2 as printl, getUUID, getVersion, getMyIp, getPlexHeaders, getOKMsg, getXMLHeader

#===============================================================================
#
#===============================================================================
class RemoteHandler(BaseHTTPRequestHandler):
	"""
	Serves a HEAD request
	"""
	session = None
	playerCallback = None
	progress = None
	currentCommandId = 0
	protocol_version = 'HTTP/1.1'

	#===========================================================================
	#
	#===========================================================================
	def do_HEAD(self):
		printl("", self, "S")

		printl("Serving HEAD request...", self, "D")
		self.answer_request()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def do_GET(self):
		printl("", self, "S")

		printl("Serving GET request...", self, "D")
		self.answer_request()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def do_OPTIONS(self):
		printl("", self, "S")

		printl("Serving OPTIONS request...", self, "D")
		self.send_response(200)
		self.send_header('Content-Length', '0')
		self.send_header('Content-Type', 'text/plain')
		self.send_header('Connection', 'close')
		self.setAccessControlHeaders()
		self.end_headers()
		self.wfile.close()

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def response(self, body, headers = {}, code = 200):
		printl("", self, "S")

		try:
			self.send_response(code)

			for key in headers:
				self.send_header(key, headers[key])

			self.send_header('Content-Length', len(body))
			self.send_header('Connection', "close")

			self.setAccessControlHeaders()

			self.end_headers()
			self.wfile.write(body)
			self.wfile.close()
		except:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def answer_request(self):
		printl("", self, "S")

		try:
			request_path=self.path[1:]
			request_path=re.sub(r"\?.*","",request_path)

			printl("request path is: [%s]" % request_path, self, "D")

			# first we get all params form url
			params = self.getParams()

			data = {"command": "updateCommandId", "uuid": self.headers.get('X-Plex-Client-Identifier', self.client_address[0]), "commandID": params.get('commandID', False)}
			self.playerCallback(data)
			self.resetCallback()

			if request_path == "player/timeline/subscribe":
				self.response(getOKMsg(), getPlexHeaders())

				protocol = params.get('protocol', False)
				host = self.client_address[0]
				port = params.get('port', False)
				uuid = self.headers.get('X-Plex-Client-Identifier', "")
				commandID = params.get('commandID', 0)

				printl("host: " + str(host), self, "D")
				printl("protocol: " + str(protocol), self, "D")
				printl("port: " + str(port), self, "D")
				printl("uuid: " + str(uuid), self, "D")
				printl("commandID: " + str(commandID), self, "D")

				data = {"command": "addSubscriber", "protocol": protocol, "host": host, "port": port, "uuid": uuid, "commandID": commandID}
				#subMgr.addSubscriber(protocol, host, port, uuid, commandID)
				self.playerCallback(data)
				self.resetCallback()

			elif "player/timeline/unsubscribe" in request_path:
				self.response(getOKMsg(), getPlexHeaders())
				uuid = self.headers.get('X-Plex-Client-Identifier', False) or self.client_address[0]
				data = {"command": "removeSubscriber", "uuid": uuid}
				#subMgr.removeSubscriber(uuid)
				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "resources":
				responseContent = getXMLHeader()
				responseContent += str(self.getResourceXml())
				self.response(responseContent, getPlexHeaders())

			elif request_path == "player/timeline/poll":
				commandID = params.get('commandID', 0)
				self.subMgr = SubscriptionManager()
				try:
					e2params = self.session.current_dialog.getPlayerState()
					if e2params:
						self.subMgr.progressFromEnigma2 = e2params['progress']
						self.subMgr.playerStateFromEnigma2 = e2params["state"]
						self.subMgr.durationFromEnigma2 = e2params["duration"]
						self.subMgr.lastkey = e2params["lastKey"]

					self.answerPoll(commandID)
					sleep(1)
				except:
					print "no params"
					self.answerPoll(commandID)
					sleep(1)

			elif request_path == "player/playback/setParameters":
				volume = params["volume"]
				data = {"command": "setVolume", "volume": volume}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/pause":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "pause"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/play":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "play"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/stop":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stop"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/skipNext":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "skipNext"}
				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/skipPrevious":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "skipPrevious"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/stepForward":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stepForward"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/stepBack":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stepBack"}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/seekTo":
				self.response(getOKMsg(), getPlexHeaders())
				offset =  params["offset"]
				data = {"command": "seekTo", "offset": offset}

				self.playerCallback(data)
				self.resetCallback()

			elif request_path == "player/playback/playMedia":
				self.response(getOKMsg(), getPlexHeaders())

				self.currentAddress = params.get('address', self.client_address[0])
				self.currentKey = params['key']
				self.currentPort = params['port']
				self.currentProtocol = params.get('protocol', "http")
				self.currentCompleteAddress = self.currentAddress + ":" + self.currentPort

				if "offset" in params:
					offset = int(params["offset"])
				else:
					offset = 0

				machineIdentifier = params["machineIdentifier"]
				printl("target machineIdentifier: " + str(machineIdentifier), self, "D")

				for serverConfig in config.plugins.dreamplex.Entries:
					printl("current machineIdentifier: " + str(serverConfig.machineIdentifier.value), self, "D")

					if machineIdentifier in serverConfig.machineIdentifier.value:

						printl("we have a match ...", self, "D")
						self.g_serverConfig = serverConfig

						self.plexInstance = Singleton().getPlexInstance(PlexLibrary(self.session, self.g_serverConfig, self.currentCompleteAddress, machineIdentifier))

						listViewList, mediaContainer = self.plexInstance.getMoviesFromSection(self.currentProtocol + "://" + self.currentAddress + ":" + self.currentPort + self.currentKey)

						autoPlayMode = False

						if offset > 0:
							forceResume = True
						else:
							forceResume = False

						resumeMode = False # this is always false because the ios and android app ask itself if we want to resume :-) no need to ask second time

						playbackMode = self.g_serverConfig.playbackType.value
						currentIndex = 0
						libraryName = "Mixed"
						splittedData = self.currentKey.split("/")
						subtitleData = self.plexInstance.getSelectedSubtitleDataById(self.currentCompleteAddress, splittedData[-1])

						data = {"command": "playMedia", "currentKey": self.currentKey, "listViewList": listViewList, "mediaContainer": mediaContainer, "autoPlayMode": autoPlayMode, "forceResume":  forceResume, "resumeMode": resumeMode, "playbackMode": playbackMode, "currentIndex": currentIndex, "libraryName": libraryName, "subtitleData": subtitleData }

						self.playerCallback(data)
						self.resetCallback()

					else:
						printl("no match ...", self, "D")

			else:
				self.response(getOKMsg(), getPlexHeaders())
		except:
				traceback.print_exc()
				self.wfile.close()

				printl("", self, "C")
				return
		try:
			self.wfile.close()
		except:
			pass

		printl("", self, "C")

	#===========================================================================
	#
	#===========================================================================
	def resetCallback(self):
		# we do this due to the fact that the messagepump is triggered mor often than we want to via playercallback for this reason we set to idle so that for example playMedia command is not called more than once
		data = {"command": "idle"}
		self.playerCallback(data)

	#===========================================================================
	#
	#===========================================================================
	def answerPoll(self, commandID):
		self.response(re.sub(r"INSERTCOMMANDID", str(commandID), self.subMgr.msg(self.getPlayers())), {
			'Access-Control-Expose-Headers': 'X-Plex-Client-Identifier',
			'Content-Type': 'text/xml'
			})

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
	def getResourceXml(self):
		printl("", self, "S")

		xml = "<MediaContainer><Player protocolCapabilities='playback, navigation' product='"+ getMyIp() +"' platformVersion='"+ getVersion() +"' platform='Enigma2' machineIdentifier='"+ getUUID() +"' title='"+ config.plugins.dreamplex.boxName.value +"' protocolVersion='1' deviceClass='stb'/></MediaContainer>"

		printl("", self, "C")
		return xml

	#===========================================================================
	#
	#===========================================================================
	def setXmlHeader(self, xml):
		printl("", self, "S")

		self.send_header('Content-type', 'text/xml; charset="utf-8"')
		self.send_header('Content-Length', str(len(xml)))

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def setAccessControlHeaders(self):
		printl("", self, "S")

		self.send_header('X-Plex-Client-Identifier', getUUID())
		self.send_header('Access-Control-Max-Age', '1209600')
		self.send_header('Access-Control-Allow-Credentials', 'true')
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
		self.send_header("Access-Control-Allow-Headers", "x-plex-client-identifier,x-plex-device,x-plex-device-name,x-plex-platform,x-plex-platform-version,x-plex-product,x-plex-target-client-identifier,x-plex-username,x-plex-version")

		printl("", self, "S")

	#===========================================================================
	#
	#===========================================================================
	def getParams(self):
		printl("", self, "S")

		params = {}
		paramarrays = parse_qs(urlparse(self.path).query)

		for key in paramarrays:
			params[key] = paramarrays[key][0]

		printl("", self, "C")
		return params

	#===========================================================================
	#
	#===========================================================================
	def getPlayers(self):
		ret = {}

		try:
			ret = self.session.current_dialog.getPlayer()
		except:
			pass

		return ret
