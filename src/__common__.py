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
import sys
import os
import datetime
import shutil
import math

from enigma import addFont, loadPNG, loadJPG
from skin import loadSkin
from Components.config import config
from Components.AVSwitch import AVSwitch

from DPH_Singleton import Singleton

#===============================================================================
# import cProfile
#===============================================================================
try:
# Python 2.5
	import xml.etree.cElementTree as etree
#printl2("running with cElementTree on Python 2.5+", __name__, "D")
except ImportError:
	try:
		# Python 2.5
		import xml.etree.ElementTree as etree
	#printl2("running with ElementTree on Python 2.5+", __name__, "D")
	except ImportError:
		#printl2("something went wrong during etree import" + str(e), self, "E")
		etree = None
		raise Exception

#===============================================================================
# CONSTANTS
#===============================================================================
gBoxType = None
STARTING_MESSAGE = ">>>>>>>>>>"
CLOSING_MESSAGE = "<<<<<<<<<<"
#===============================================================================
# 
#===============================================================================
def printl2(string, parent=None, dmode="U", obfuscate=False, steps=4):
	"""
	@param string:
	@param parent:
	@param dmode: default = "U" undefined 
							"E" shows error
							"W" shows warning
							"I" shows important information to have better overview if something really happening or not
							"D" shows additional debug information for better debugging
							"S" shows started functions/classes etc.
							"C" shows closing functions/classes etc.
	@return: none
	"""

	debugMode = config.plugins.dreamplex.debugMode.value

	if debugMode:

		offset = string.find("X-Plex-Token")
		if not string.find("X-Plex-Token") == -1:
			steps = 8
			start = offset + 13
			end = start + steps
			new_string = string[0:start] + "********" + string[end:]
			string = new_string

		if obfuscate is True:
			string = string[:-steps]
			for i in range(steps):
				string += "*"

		if parent is None:
			out = str(string)
		else:
			classname = str(parent.__class__).rsplit(".", 1)
			if len(classname) == 2:
				classname = classname[1]
				classname = classname.rstrip("\'>")
				classname += "::"
				out = str(classname) + str(sys._getframe(1).f_code.co_name) + " -> " + str(string)
			else:
				out = str(parent) + " -> " + str(string)

		if dmode == "E":
			print "[DreamPlex] " + "E" + "  " + str(out)
			writeToLog(dmode, out)

		elif dmode == "W":
			print "[DreamPlex] " + "W" + "  " + str(out)
			writeToLog(dmode, out)

		elif dmode == "I":
			print "[DreamPlex] " + "I" + "  " + str(out)
			writeToLog(dmode, out)

		elif dmode == "D":
			print "[DreamPlex] " + "D" + "  " + str(out)
			writeToLog(dmode, out)

		elif dmode == "S":
			print "[DreamPlex] " + "S" + "  " + str(out) + STARTING_MESSAGE
			writeToLog(dmode, out + STARTING_MESSAGE)

		elif dmode == "C":
			print "[DreamPlex] " + "C" + "  " + str(out) + CLOSING_MESSAGE
			writeToLog(dmode, out + CLOSING_MESSAGE)

		elif dmode == "U":
			print "[DreamPlex] " + "U  specify me!!!!!" + "  " + str(out)
			writeToLog(dmode, out)

		elif dmode == "X":
			print "[DreamPlex] " + "D" + "  " + str(out)
			writeToLog(dmode, out)

		else:
			print "[DreamPlex] " + "OLD CHARACTER CHANGE ME !!!!!" + "  " + str(out)

#===============================================================================
# 
#===============================================================================
def writeToLog(dmode, out):
	"""
	singleton handler for the log file
	
	@param dmode: E, W, S, H, A, C, I
	@param out: message string
	@return: none
	"""
	try:
		instance = Singleton()
		if instance.getLogFileInstance() is "":
			openLogFile()
			gLogFile = instance.getLogFileInstance()
			gLogFile.truncate()
		else:
			gLogFile = instance.getLogFileInstance()

		now = datetime.datetime.now()
		gLogFile.write("%02d:%02d:%02d.%07d " % (now.hour, now.minute, now.second, now.microsecond) + " >>> " + str(
			dmode) + " <<<  " + str(out) + "\n")
		gLogFile.flush()

	except Exception, ex:
		printl2("Exception(" + str(type(ex)) + "): " + str(ex), "__common__::writeToLog", "E")


#===============================================================================
# 
#===============================================================================
def openLogFile():
	"""
	singleton instance for logfile
	"""
	#printl2("", "openLogFile", "S")

	logDir = config.plugins.dreamplex.logfolderpath.value

	try:
		if os.path.exists(logDir + "dreamplex_former.log"):
			os.remove(logDir + "dreamplex_former.log")

		if os.path.exists(logDir + "dreamplex.log"):
			shutil.copy2(logDir + "dreamplex.log", logDir + "dreamplex_former.log")

		instance = Singleton()
		instance.getLogFileInstance(open(logDir + "dreamplex.log", "w"))

	except Exception, ex:
		printl2("Exception(" + str(type(ex)) + "): " + str(ex), "openLogFile", "E")

	#printl2("", "openLogFile", "C")

#===============================================================================
# 
#===============================================================================
def testInetConnectivity(target="http://www.google.com"):
	"""
	test if we get an answer from the specified url
	
	@param target:
	@return: bool
	"""
	printl2("", "__common__::testInetConnectivity", "S")

	import urllib2
	from   sys import version_info
	import socket

	try:
		opener = urllib2.build_opener()

		if version_info[1] >= 6:
			page = opener.open(target, timeout=2)
		else:
			socket.setdefaulttimeout(2)
			page = opener.open(target)
		if page is not None:

			printl2("", "__common__::testInetConnectivity", "C")
			return True
		else:

			printl2("", "__common__::testInetConnectivity", "C")
			return False
	except:

		printl2("", "__common__::testInetConnectivity", "C")
		return False

#===============================================================================
# 
#===============================================================================
def testPlexConnectivity(ip, port):
	"""
	test if the plex server is online on the specified port
	
	@param ip: e.g. 192.168.0.1
	@param port: e.g. 32400
	@return: bool
	"""
	printl2("", "__common__::testPlexConnectivity", "S")

	import socket

	sock = socket.socket()

	printl2("IP => " + str(ip), "__common__::testPlexConnectivity", "I")
	printl2("PORT => " + str(port), "__common__::testPlexConnectivity", "I")

	try:
		sock.settimeout(5)
		sock.connect((ip, port))
		sock.close()

		printl2("", "__common__::testPlexConnectivity", "C")
		return True
	except socket.error, e:
		printl2("Strange error creating socket: %s" % e, "__common__::testPlexConnectivity", "E")
		sock.close()

		printl2("", "__common__::testPlexConnectivity", "C")
		return False


#===============================================================================
# 
#===============================================================================	
def registerPlexFonts():
	"""
	registers fonts for skins
	
	@param: none 
	@return none
	"""
	printl2("", "__common__::registerPlexFonts", "S")

	printl2("adding fonts", "__common__::registerPlexFonts", "I")

	tree = Singleton().getSkinParamsInstance()
	#tree = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
	for font in tree.findall('font'):
		path = str(font.get('path'))
		printl2("path: " + str(font.get('path')), "__common__::registerPlexFonts", "D")

		size = int(font.get('size'))
		printl2("size: " + str(font.get('size')), "__common__::registerPlexFonts", "D")

		name = str(font.get('name'))
		printl2("name: " + str(font.get('name')), "__common__::registerPlexFonts", "D")

		addFont(path, name, size, False)
		printl2("added => " + name, "__common__::registerPlexFonts", "I")

	printl2("", "__common__::registerPlexFonts", "C")

#===============================================================================
# 
#===============================================================================
def loadPlexSkin():
	"""
	loads the corresponding skin.xml file
	
	@param: none 
	@return none
	"""
	printl2("", "__common__::loadPlexSkin", "S")
	printl2("current skin: " + str(config.plugins.dreamplex.skins.value), "__common__::loadPlexSkin", "S")

	skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value + "/1280x720/skin.xml"

	if skin:
		loadSkin(skin)

	printl2("", "__common__::loadPlexSkin", "C")

#===============================================================================
# 
#===============================================================================
def checkPlexEnvironment():
	"""
	checks needed file structure for plex
	
	@param: none 
	@return none	
	"""
	printl2("", "__common__::checkPlexEnvironment", "S")

	playerTempFolder = config.plugins.dreamplex.playerTempPath.value
	logFolder = config.plugins.dreamplex.logfolderpath.value
	mediaFolder = config.plugins.dreamplex.mediafolderpath.value
	configFolder = config.plugins.dreamplex.configfolderpath.value
	cacheFolder = config.plugins.dreamplex.cachefolderpath.value

	checkDirectory(playerTempFolder)
	checkDirectory(logFolder)
	checkDirectory(mediaFolder)
	checkDirectory(configFolder)
	checkDirectory(cacheFolder)

	printl2("", "__common__::checkPlexEnvironment", "C")

#===============================================================================
# 
#===============================================================================
def checkDirectory(directory):
	"""
	checks if dir exists. if not it is added
	
	@param directory: e.g. /media/hdd/
	@return: none
	"""
	printl2("", "__common__::checkDirectory", "S")
	printl2("checking ... " + directory, "__common__::checkDirectory", "D")

	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
			printl2("directory not found ... added", "__common__::checkDirectory", "D")
		else:
			printl2("directory found ... nothing to do", "__common__::checkDirectory", "D")

	except Exception, ex:
		printl2("Exception(" + str(type(ex)) + "): " + str(ex), "__common__::checkDirectory", "E")

	printl2("", "__common__::checkDirectory", "C")

#===============================================================================
# 
#===============================================================================		
def getServerFromURL(url): # CHECKED
	"""
	Simply split the URL up and get the server portion, sans port
	
	@param url: with or without protocol
	@return: the server URL
	"""
	printl2("", "__common__::getServerFromURL", "S")

	if url[0:4] == "http" or url[0:4] == "plex":

		printl2("", "__common__::getServerFromURL", "C")
		return url.split('/')[2]
	else:

		printl2("", "__common__::getServerFromURL", "C")
		return url.split('/')[0]

#===============================================================================
# 
#===============================================================================
def getBoxInformation():
	printl2("", "__common__::getBoxtype", "C")
	global gBoxType

	if gBoxType is not None:

		printl2("", "__common__::getBoxtype", "C")
		return gBoxType
	else:
		gBoxType = setBoxInformation()

		printl2("", "__common__::getBoxtype", "C")
		return gBoxType

#===============================================================================
# 
#===============================================================================
def setBoxInformation():
	printl2("", "__common__::_setBoxtype", "C")

	try:
		filePointer = open("/proc/stb/info/model")
	except:
		filePointer = open("/hdd/model")

	box = filePointer.readline().strip()
	filePointer.close()
	manu = "Unknown"
	model = box # "UNKNOWN" # Fallback to internal string
	arch = "sh4" # "unk" # Its better so set the arch by default to unkown so no wrong update information will be displayed

	if box == "ufs910":
		manu = "Kathrein"
		model = "UFS-910"
		arch = "sh4"
	elif box == "ufs912":
		manu = "Kathrein"
		model = "UFS-912"
		arch = "sh4"
	elif box == "ufs922":
		manu = "Kathrein"
		model = "UFS-922"
		arch = "sh4"
	elif box == "tf7700hdpvr":
		manu = "Topfield"
		model = "HDPVR-7700"
		arch = "sh4"
	elif box == "dm800":
		manu = "Dreambox"
		model = "800"
		arch = "mipsel"
	elif box == "dm800se":
		manu = "Dreambox"
		model = "800se"
		arch = "mipsel"
	elif box == "dm8000":
		manu = "Dreambox"
		model = "8000"
		arch = "mipsel"
	elif box == "dm500hd":
		manu = "Dreambox"
		model = "500hd"
		arch = "mipsel"
	elif box == "dm7025":
		manu = "Dreambox"
		model = "7025"
		arch = "mipsel"
	elif box == "dm7020hd":
		manu = "Dreambox"
		model = "7020hd"
		arch = "mipsel"
	elif box == "elite":
		manu = "Azbox"
		model = "Elite"
		arch = "mipsel"
	elif box == "premium":
		manu = "Azbox"
		model = "Premium"
		arch = "mipsel"
	elif box == "premium+":
		manu = "Azbox"
		model = "Premium+"
		arch = "mipsel"
	elif box == "cuberevo-mini":
		manu = "Cubarevo"
		model = "Mini"
		arch = "sh4"
	elif box == "hdbox":
		manu = "Fortis"
		model = "HdBox"
		arch = "sh4"

	if arch == "mipsel":
		version = getBoxArch()
	else:
		version = "duckbox"

	boxData = (manu, model, arch, version)
	printl2("", "__common__::_setBoxtype", "C")
	return boxData

#===============================================================================
# 
#===============================================================================
def getBoxArch():
	printl2("", "__common__::getBoxArch", "S")

	ARCH = "unknown"

	if (2, 6, 8) > sys.version_info > (2, 6, 6):
		ARCH = "oe16"

	if (2, 7, 4) > sys.version_info > (2, 7, 0):
		ARCH = "oe20"

	printl2("", "__common__::getBoxArch", "C")
	return ARCH

#===============================================================================
#
#===============================================================================
def prettyFormatTime(msec):
	printl2("", "__common__::prettyFormatTime", "S")

	seconds = msec / 1000
	hours = seconds // (60 * 60)
	seconds %= (60 * 60)
	minutes = seconds // 60
	seconds %= 60
	hrstr = "hour"
	minstr = "min"
	secstr = "sec"

	if hours != 1:
		hrstr += "s"

	if minutes != 1:
		minstr += "s"

	if seconds != 1:
		secstr += "s"

	if hours > 0:
		printl2("", "__common__::prettyFormatTime", "C")
		return "%i %s %02i %s %02i %s" % (hours, hrstr, minutes, minstr, seconds, secstr)

	elif minutes > 0:
		printl2("", "__common__::prettyFormatTime", "C")
		return "%i %s %02i %s" % (minutes, minstr, seconds, secstr)

	else:
		printl2("", "__common__::prettyFormatTime", "C")
		return "%i %s" % (seconds, secstr)

#===============================================================================
#
#===============================================================================
def formatTime(msec):
	printl2("", "__common__::formatTime", "S")

	seconds = msec / 1000
	hours = seconds // (60 * 60)
	seconds %= (60 * 60)
	minutes = seconds // 60
	seconds %= 60

	if hours > 0:
		printl2("", "__common__::formatTime", "C")
		return "%i:%02i:%02i" % (hours, minutes, seconds)

	elif minutes > 0:
		printl2("", "__common__::formatTime", "C")
		return "%i:%02i" % (minutes, seconds)

	else:
		printl2("", "__common__::formatTime", "C")
		return "%i" % seconds

#===============================================================================
# 
#===============================================================================
def getScale():
	printl2("", "__common__::getScale", "S")

	printl2("", "__common__::getScale", "C")
	return AVSwitch().getFramebufferScale()

#===========================================================================
# 
#===========================================================================
def checkXmlFile(location):
	printl2("", "__common__::checkXmlFile", "S")

	if not os.path.isfile(location):
		printl2("xml file not found, generating ...", "__common__::checkXmlFile", "D")
		with open(location, "a") as writefile:
			writefile.write("<xml></xml>")
			printl2("writing xml file done", "__common__::checkXmlFile", "D")

	else:
		printl2("found xml file, nothing to do", "__common__::checkXmlFile", "D")

	printl2("", "__common__::checkXmlFile", "C")

#===========================================================================
# 
#===========================================================================
def getXmlContent(location):
	printl2("", "__common__::getXmlContent", "S")

	checkXmlFile(location)

	xml = open(location).read()
	printl2("xml: " + str(xml), "__common__::getXmlContent", "D")

	tree = None

	try:
		tree = etree.fromstring(xml)
	except Exception, e:
		printl2("something weng wrong during xml parsing" + str(e), __name__, "E")

	printl2("", "__common__::getXmlContent", "C")
	return tree

#===========================================================================
# 
#===========================================================================
def writeXmlContent(content, location):
	printl2("", "__common__::writeXmlContent", "S")

	indented = indentXml(content)
	xmlString = etree.tostring(indented)
	fobj = open(location, "w")
	fobj.write(xmlString)
	fobj.close()
	printl2("xmlString: " + str(xmlString), "__common__::getXmlContent", "C")

	printl2("", "__common__::getXmlContent", "C")


#===========================================================================
# 
#===========================================================================
def indentXml(elem, level=0, more_sibs=False):
	printl2("", "__common__::indentXml", "S")

	i = "\n"
	if level:
		i += (level - 1) * '  '
	num_kids = len(elem)
	if num_kids:
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
			if level:
				elem.text += '  '
		count = 0
		for kid in elem:
			indentXml(kid, level + 1, count < num_kids - 1)
			count += 1
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
			if more_sibs:
				elem.tail += '  '
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i
			if more_sibs:
				elem.tail += '  '

	printl2("", "__common__::indentXml", "C")
	return elem

#===========================================================================
# 
#===========================================================================	
def convertSize(size):
	printl2("", "__common__::convertSize", "S")

	size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size, 1024)))
	p = math.pow(1024, i)
	s = round(size / p, 2)

	if s > 0:
		printl2("", "__common__::convertSize", "C")
		return '%s %s' % (s, size_name[i])
	else:
		printl2("", "__common__::convertSize", "C")
		return '0B'

#===========================================================================
# 
#===========================================================================
def loadPicture(filename):
	printl2("", "__common__::loadPicture", "S")
	ptr = None
	if filename is None:
		printl2("", "__common__::loadPicture", "C")
		return ptr

	if filename[-4:] == ".png":
		ptr = loadPNG(filename)
	elif filename[-4:] == ".jpg":
		ptr = loadJPG(filename)
		if not ptr:
			# kind of fallback if filetype is declared wrong
			ptr = loadPNG(filename)
	printl2("filename: " + str(filename), "__common__::loadPicture", "D")
	printl2("", "__common__::loadPicture", "C")
	return ptr

#===========================================================================
#
#===========================================================================
def getPlexHeader(g_sessionID, asString = True):
	printl2("", "__common__::getPlexHeader", "S")

	boxData = getBoxInformation()

	if asString:
		plexHeader={'X-Plex-Platform': "Enigma2",
					'X-Plex-Platform-Version': boxData[3],
					'X-Plex-Provides': "player",
					'X-Plex-Product': "DreamPlex",
					'X-Plex-Version': "1",
					'X-Plex-Device': boxData[0],
					'X-Plex-Client-Identifier': g_sessionID,
					'X-Plex-Device-Name': boxData[1]}
	else:
		plexHeader = []
		plexHeader.append('X-Plex-Platform: Enigma2')
		plexHeader.append('X-Plex-Platform-Version: ' + boxData[3])
		plexHeader.append('X-Plex-Provides: player')
		plexHeader.append('X-Plex-Product: DreamPlex')
		plexHeader.append('X-Plex-Version: 1')
		plexHeader.append('X-Plex-Device: ' +  boxData[0])
		plexHeader.append('X-Plex-Client-Identifier: ' + g_sessionID)

	printl2("", "__common__::getPlexHeader", "C")
	return plexHeader