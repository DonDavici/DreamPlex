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
import urllib
import threading
import httplib
import traceback
import string

from time import sleep
from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler

from Components.config import config

from DPH_Singleton import Singleton
from DP_PlexLibrary import PlexLibrary

from __common__ import printl2 as printl, getUUID, getVersion, getMyIp, timeToMillis

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
			self.send_response(200)

			request_path=self.path[1:]
			request_path=re.sub(r"\?.*","",request_path)

			printl("request path is: [%s]" % request_path, self, "D")

			# first we get all params form url
			params = self.getParams()

			subMgr.updateCommandID(self.headers.get('X-Plex-Client-Identifier', self.client_address[0]), params.get('commandID', False))

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

				subMgr.addSubscriber(protocol, host, port, uuid, commandID)

			elif "player/timeline/unsubscribe" in request_path:
				self.response(getOKMsg(), getPlexHeaders())
				uuid = self.headers.get('X-Plex-Client-Identifier', False) or self.client_address[0]
				subMgr.removeSubscriber(uuid)

			elif request_path == "resources":
				responseContent = getXMLHeader()
				responseContent += str(self.getResourceXml())
				self.response(responseContent, getPlexHeaders())

			elif request_path == "player/timeline/poll":
				if params.get('wait', False) == '1':
					sleep(950)
				commandID = params.get('commandID', 0)
				self.response(re.sub(r"INSERTCOMMANDID", str(commandID), subMgr.msg(getPlayers())), {
				'Access-Control-Expose-Headers': 'X-Plex-Client-Identifier',
				'Content-Type': 'text/xml'
				})

			elif request_path == "playerProgress":
				subMgr.progressFromEnigma2 = params['progress']
				subMgr.playerStateFromEnigma2 = params["state"]
				subMgr.durationFromEnigma2 = params["duration"]
				subMgr.lastkey = params["lastKey"]
				#subMgr.notify()

			elif request_path == "player/playback/setParameters":
				volume = params["volume"]
				data = {"command": "setVolume", "volume": volume}

				self.playerCallback(data)

			elif request_path == "player/playback/pause":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "pause"}

				self.playerCallback(data)

			elif request_path == "player/playback/play":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "play"}

				self.playerCallback(data)

			elif request_path == "player/playback/stop":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stop"}

				self.playerCallback(data)

			elif request_path == "player/playback/skipNext":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "skipNext"}
				self.playerCallback(data)

			elif request_path == "player/playback/skipPrevious":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "skipPrevious"}

				self.playerCallback(data)

			elif request_path == "player/playback/stepForward":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stepForward"}

				self.playerCallback(data)

			elif request_path == "player/playback/stepBack":
				self.response(getOKMsg(), getPlexHeaders())
				data = {"command": "stepBack"}

				self.playerCallback(data)

			elif request_path == "player/playback/seekTo":
				self.response(getOKMsg(), getPlexHeaders())
				offset =  params["offset"]
				data = {"command": "seekTo", "offset": offset}

				self.playerCallback(data)

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

						data = {"listViewList": listViewList, "mediaContainer": mediaContainer, "autoPlayMode": autoPlayMode, "forceResume":  forceResume, "resumeMode": resumeMode, "playbackMode": playbackMode, "currentIndex": currentIndex, "libraryName": libraryName, "subtitleData": subtitleData }

						self.playerCallback(data)

					else:
						printl("no match ...", self, "D")

			else:
				self.send_response(200)
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
class SubscriptionManager:
	def __init__(self):
		self.subscribers = {}
		self.info = {}
		self.lastkey = ""
		self.volume = 0
		self.guid = ""
		self.server = ""
		self.protocol = "http"
		self.port = ""
		self.playerprops = {}
		self.sentstopped = True
		self.progressFromEnigma2 = 0
		self.playerStateFromEnigma2 = "stopped"
		self.durationFromEnigma2 = 0

	#===========================================================================
	#
	#===========================================================================
	def getVolume(self):

		self.volume = 100

	#===========================================================================
	#
	#===========================================================================
	def msg(self, players):
		msg = getXMLHeader()
		msg += '<MediaContainer commandID="INSERTCOMMANDID"'

		if players:
			self.getVolume()
			maintype = "music"
			for p in players.values():
				maintype = p.get('type')
			self.mainlocation = "fullScreen" + maintype[0:1].upper() + maintype[1:].lower()
		else:
			self.mainlocation = "navigation"
		msg += ' location="%s">' % self.mainlocation

		msg += self.getTimelineXML(getAudioPlayerId(players), "music")
		msg += self.getTimelineXML(getPhotoPlayerId(players), "photo")
		msg += self.getTimelineXML(getVideoPlayerId(players), "video")
		msg += "\r\n</MediaContainer>"
		return msg

	#===========================================================================
	#
	#===========================================================================
	def getTimelineXML(self, playerid, ptype):
		if playerid > 0:
			#info = self.getPlayerProperties(playerid)
			# save this info off so the server update can use it too
			#self.playerprops[playerid] = info;
			state = "playing"
			time = self.progressFromEnigma2
		else:
			state = "stopped"
			time = 0

		ret = "\r\n"+'<Timeline location="%s" state="%s" time="%s" type="%s"' % (self.mainlocation, state, time, ptype)

		if playerid > 0:
			#serv = {}#getServerByHost(self.server)
			ret += ' duration="%s"' % self.durationFromEnigma2
			ret += ' seekRange="0-%s"' % self.progressFromEnigma2
			ret += ' controllable="%s"' % self.controllable()
			ret += ' machineIdentifier="%s"' % getUUID() #serv.get('uuid', "")
			ret += ' protocol="%s"' % self.protocol
			ret += ' address="%s"' % self.server
			ret += ' port="%s"' % self.port
			ret += ' guid="%s"' % 11111 #info['guid']
			ret += ' containerKey="%s"' % (self.lastkey or "/library/metadata/900000")
			ret += ' key="%s"' % (self.lastkey or "/library/metadata/900000")
			m = re.search(r'(\d+)$', self.lastkey)
			if m:
				ret += ' ratingKey="%s"' % m.group()
			ret += ' volume="%s"' % 100
			ret += ' shuffle="%s"' % 0

		ret += '/>'
		return ret

	#===========================================================================
	#
	#===========================================================================
	def updateCommandID(self, uuid, commandID):
		if commandID and self.subscribers.get(uuid, False):
			self.subscribers[uuid].commandID = int(commandID)

	#===========================================================================
	#
	#===========================================================================
	def notify(self, event = False):
		self.cleanup()
		players = getPlayers()
		# fetch the message, subscribers or not, since the server
		# will need the info anyway
		msg = self.msg(players)

		if self.subscribers:
			with threading.RLock():
				for sub in self.subscribers.values():
					sub.send_update(msg, len(players)==0)

		# we do not use this because our player is informing the server
		#self.notifyServer(players)
		return True

	#===========================================================================
	#
	#===========================================================================
	def notifyServer(self, players):
		if not players and self.sentstopped:
			return True

		params = {'state': 'stopped'}

		for p in players.values():
			params = {}
			params['containerKey'] = (self.lastkey or "/library/metadata/900000")
			params['key'] = (self.lastkey or "/library/metadata/900000")
			m = re.search(r'(\d+)$', self.lastkey)
			if m:
				params['ratingKey'] = m.group()
			params['state'] = self.playerStateFromEnigma2
			params['time'] = self.progressFromEnigma2
			params['duration'] = self.durationFromEnigma2

		requests.getwithparams(self.server, self.port, "/:/timeline", params, getPlexHeaders())
		printl("sent server notification with state = %s" % params['state'], self, "D")

		if players:
			self.sentstopped = False
		else:
			self.sentstopped = True

	#===========================================================================
	#
	#===========================================================================
	def controllable(self):
		return "playPause,play,stop,skipPrevious,skipNext,volume,stepBack,stepForward,seekTo"

	#===========================================================================
	#
	#===========================================================================
	def addSubscriber(self, protocol, host, port, uuid, commandID):
		sub = Subscriber(protocol, host, port, uuid, commandID)
		with threading.RLock():
			self.subscribers[sub.uuid] = sub
		return sub

	#===========================================================================
	#
	#===========================================================================
	def removeSubscriber(self, uuid):
		with threading.RLock():
			for sub in self.subscribers.values():
				if sub.uuid == uuid or sub.host == uuid:
					sub.cleanup()
					del self.subscribers[sub.uuid]

	#===========================================================================
	#
	#===========================================================================
	def cleanup(self):
		with threading.RLock():
			for sub in self.subscribers.values():
				if sub.age > 30:
					sub.cleanup()
					del self.subscribers[sub.uuid]

	#===========================================================================
	#
	#===========================================================================
	def getPlayerProperties(self, playerid):
		info = {}
		try:
			# get info from the player
			props = {}#jsonrpc("Player.GetProperties", {"playerid": playerid, "properties": ["time", "totaltime", "speed", "shuffled"]})
			info['time'] = timeToMillis(props['time'])
			info['duration'] = timeToMillis(props['totaltime'])
			info['state'] = ("paused", "playing")[int(props['speed'])]
			info['shuffle'] = ("0","1")[props.get('shuffled', False)]
		except:
			info['time'] = 0
			info['duration'] = 0
			info['state'] = "stopped"
			info['shuffle'] = False
		# get the volume from the application
		info['volume'] = self.volume
		info['guid'] = self.guid

		return info

#===========================================================================
#
#===========================================================================
class Subscriber:
	#===========================================================================
	#
	#===========================================================================
	def __init__(self, protocol, host, port, uuid, commandID):
		self.protocol = protocol or "http"
		self.host = host
		self.port = port or 32400
		self.uuid = uuid or host
		self.commandID = int(commandID) or 0
		self.navlocationsent = False
		self.age = 0

	#===========================================================================
	#
	#===========================================================================
	def __eq__(self, other):
		return self.uuid == other.uuid

	#===========================================================================
	#
	#===========================================================================
	def tostr(self):
		return "uuid=%s,commandID=%i" % (self.uuid, self.commandID)

	#===========================================================================
	#
	#===========================================================================
	def cleanup(self):
		requests.closeConnection(self.protocol, self.host, self.port)

	#===========================================================================
	#
	#===========================================================================
	def send_update(self, msg, is_nav):
		self.age += 1
		if not is_nav:
			self.navlocationsent = False
		elif self.navlocationsent:
			return True
		else:
			self.navlocationsent = True
		msg = re.sub(r"INSERTCOMMANDID", str(self.commandID), msg)
		printl("sending xml to subscriber %s: %s" % (self.tostr(), msg), self, "D")
		requests.post(self.host, self.port, "/:/timeline", msg, getPlexHeaders(), self.protocol)
		# if not requests.post(self.host, self.port, "/:/timeline", msg, getPlexHeaders(), self.protocol):
		# 	printl("removing subcriber ...", self, "D")
		# 	subMgr.removeSubscriber(self.uuid)

subMgr = SubscriptionManager()

#===========================================================================
#
#===========================================================================
class RequestMgr:
	def __init__(self):
		self.conns = {}

	#===========================================================================
	#
	#===========================================================================
	def getConnection(self, protocol, host, port):
		conn = self.conns.get(protocol+host+str(port), False)
		if not conn:
			if protocol=="https":
				conn = httplib.HTTPSConnection(host, port)
			else:
				conn = httplib.HTTPConnection(host, port)
		return conn

	#===========================================================================
	#
	#===========================================================================
	def closeConnection(self, protocol, host, port):
		conn = self.conns.get(protocol+host+str(port), False)
		if conn:
			conn.close()
			self.conns.pop(protocol+host+str(port), None)

	#===========================================================================
	#
	#===========================================================================
	def dumpConnections(self):
		for conn in self.conns.values():
			conn.close()
		self.conns = {}

	#===========================================================================
	#
	#===========================================================================
	def post(self, host, port, path, body, header={}, protocol="http"):
		conn = None
		try:
			conn = self.getConnection(protocol, host, port)
			header['Connection'] = "keep-alive"
			conn.request("POST", path, body, header)
			data = conn.getresponse()

			if int(data.status) >= 400:
				print "HTTP response error: " + str(data.status)
				# this should return false, but I'm hacking it since iOS returns 404 no matter what
				return data or True
			elif int(data.status) == 200:
				print "got 200 OK"
				print "data: " + str(data.read())
			else:
				return data.read() or True
		except:
			print "Unable to connect to %s\nReason:" % host
			traceback.print_exc()
			self.conns.pop(protocol+host+str(port), None)
			if conn:
				conn.close()
			return False

	#===========================================================================
	#
	#===========================================================================
	def getwithparams(self, host, port, path, params, header={}, protocol="http"):
		newpath = path + '?'
		pairs = []
		for key in params:
			pairs.append(str(key)+'='+str(params[key]))
		newpath += string.join(pairs, '&')
		return self.get(host, port, newpath, header, protocol)

	#===========================================================================
	#
	#===========================================================================
	def get(self, host, port, path, header={}, protocol="http"):
		try:
			conn = self.getConnection(protocol, host, port)
			header['Connection'] = "keep-alive"
			conn.request("GET", path, headers=header)
			data = conn.getresponse()
			if int(data.status) >= 400:
				print "HTTP response error: " + str(data.status)
				return False
			else:
				return data.read() or True
		except:
			print "Unable to connect to %s\nReason: %s" % (host, traceback.print_exc())
			self.conns.pop(protocol+host+str(port), None)
			conn.close()
			return False

requests = RequestMgr()

#===========================================================================
#
#===========================================================================
def getXMLHeader():
	printl("", "getXMLHeader", "S")

	printl("", "getXMLHeader", "C")
	return '<?xml version="1.0" encoding="utf-8"?>'+"\r\n"

#===========================================================================
#
#===========================================================================
def getOKMsg():
	printl("", "getOKMsg", "S")

	printl("", "getOKMsg", "C")
	return getXMLHeader() + '<Response code="200" status="OK" />'

#===========================================================================
#
#===========================================================================
def getPlexHeaders():
	printl("", "getPlexHeaders", "S")

	plexHeader = {
		"Content-type": "application/x-www-form-urlencoded",
		"X-Plex-Version": getVersion(),
		"X-Plex-Client-Identifier": getUUID(),
		"X-Plex-Provides": "player",
		"X-Plex-Product": "DreamPlex",
		"X-Plex-Device-Name": config.plugins.dreamplex.boxName.value,
		"X-Plex-Platform": "Enigma2",
		"X-Plex-Model": "Enigma2",
		"X-Plex-Device": "stb",
	}

	# if settings['myplex_user']:
	# plexHeader["X-Plex-Username"] = settings['myplex_user']

	printl("", "getPlexHeaders", "C")
	return plexHeader

#===========================================================================
#
#===========================================================================
def getPlayers():
	player = {}
	ret = {}

	player['playerid'] = int(1)
	player['type'] = "video"
	ret["video"] = player

	return ret

#===========================================================================
#
#===========================================================================
def getPlayerIds():
	ret = []

	for player in getPlayers().values():
		ret.append(player['playerid'])

	return ret

#===========================================================================
#
#===========================================================================
def getVideoPlayerId(players = False):
	if players is None:
		players = getPlayers()

	return players.get("video", {}).get('playerid', 0)

#===========================================================================
#
#===========================================================================
def getAudioPlayerId(players = False):
	if players is None:
		players = getPlayers()

	return players.get("music", {}).get('playerid', 0)

#===========================================================================
#
#===========================================================================
def getPhotoPlayerId(players = False):
	if players is None:
		players = getPlayers()

	return players.get("photo", {}).get('playerid', 0)
