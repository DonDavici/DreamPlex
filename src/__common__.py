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
import uuid

from enigma import addFont, loadPNG, loadJPG, getDesktop
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
version = "0.1"
boxResoltion = None
skinAuthors = ""
skinResolution = "HD"
skinCompatibility = "v2"
skinDebugMode = False
skinHighlightedColor = "#e69405"
skinNormalColor = "#ffffff"
g_boxData = None
screens = []
liveTv = None
g_uuid = None
g_oeVersion = None
g_archType = None
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
def getVersion():
	return str(version)

#===============================================================================
#
#===============================================================================
def getSkinAuthors():
	return skinAuthors

#===============================================================================
#
#===============================================================================
def getSkinHighlightedColor():
	return skinHighlightedColor

#===============================================================================
#
#===============================================================================
def getSkinNormalColor():
	return skinNormalColor

#===============================================================================
#
#===============================================================================
def getSkinCompatibility():
	return skinCompatibility

#===============================================================================
#
#===============================================================================
def getSkinDebugMode():
	return skinDebugMode

#===============================================================================
#
#===============================================================================
def getSkinResolution():
	return skinResolution

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
	if config.plugins.dreamplex.writeDebugFile.value:
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
			config.plugins.dreamplex.writeDebugFile.value = False
			config.plugins.dreamplex.debugMode.save()

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
			printl2("success, returning TRUE", "__common__::testInetConnectivity", "D")
			printl2("", "__common__::testInetConnectivity", "C")
			return True
		else:
			printl2("failure, returning FALSE", "__common__::testInetConnectivity", "D")
			printl2("", "__common__::testInetConnectivity", "C")
			return False
	except:
		printl2("exception, returning FALSE", "__common__::testInetConnectivity", "D")
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

	printl2("adding fonts", "__common__::registerPlexFonts", "D")

	tree = Singleton().getSkinParamsInstance()

	for font in tree.findall('font'):
		path = str(font.get('path'))
		printl2("path: " + str(font.get('path')), "__common__::registerPlexFonts", "D")

		size = int(font.get('size'))
		printl2("size: " + str(font.get('size')), "__common__::registerPlexFonts", "D")

		name = str(font.get('name'))
		printl2("name: " + str(font.get('name')), "__common__::registerPlexFonts", "D")

		addFont(path, name, size, False)
		printl2("added => " + name, "__common__::registerPlexFonts", "D")

	printl2("", "__common__::registerPlexFonts", "C")

#===============================================================================
#
#===============================================================================
def getBoxResolution():
	printl2("", "__common__::getBoxResolution", "S")
	global boxResoltion

	if boxResoltion is None:
		screenwidth = getDesktop(0).size().width()

		if screenwidth and screenwidth == 1920:
			boxResoltion = "FHD"
		else:
			boxResoltion = "HD"

	printl2("", "__common__::getBoxResolution", "C")
	return boxResoltion

#===============================================================================
#
#===============================================================================
def loadSkinParams():
	printl2("", "__common__::loadSkinParams", "S")

	global skinAuthors
	global skinCompatibility
	global skinResolution
	global skinDebugMode
	global skinHighlightedColor
	global skinNormalColor

	tree = Singleton().getSkinParamsInstance()

	for skinParams in tree.findall('skinParams'):
		skinCompatibility = str(skinParams.get('compatibility'))
		skinAuthors = str(skinParams.get('skinner'))
		skinResolution = str(skinParams.get('resolution'))
		skinDebugMode = str(skinParams.get('debugMode'))
		skinHighlightedColor = str(skinParams.get('highlighted'))
		skinNormalColor = str(skinParams.get('normal'))

	printl2("", "__common__::loadSkinParams", "C")

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

	skinName = str(config.plugins.dreamplex.skin.value)
	printl2("current skin: " + skinName, "__common__::loadPlexSkin", "S")

	# if we are the our default we switch automatically between the resolutions
	if skinName == "default":
		myType = getBoxResolution()
		if myType == "FHD":
			skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "_FHD/skin.xml"
		else:
			skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "/skin.xml"

	# if not we load whatever is set
	else:
		skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skin.value + "/skin.xml"

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
	homeUsersFolder = config.plugins.dreamplex.configfolderpath.value + "homeUsers"

	checkDirectory(playerTempFolder)
	checkDirectory(logFolder)
	checkDirectory(mediaFolder)
	checkDirectory(configFolder)
	checkDirectory(cacheFolder)
	checkDirectory(homeUsersFolder)

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
	"""
	@return: manu, model, arch, version
	"""
	printl2("", "__common__::getBoxtype", "S")

	if g_boxData is  None:
		setBoxInformation()

	printl2("", "__common__::getBoxtype", "C")
	return g_boxData

#===============================================================================
#
#===============================================================================
def getUUID():
	printl2("", "__common__::getUUID", "S")
	global g_uuid

	if g_uuid is None:
		g_uuid = str(uuid.uuid4())

	printl2("", "__common__::getUUID", "C")
	return str(g_uuid)

#===============================================================================
# 
#===============================================================================
def setBoxInformation():
	printl2("", "__common__::_setBoxtype", "C")

	success = False
	try:
		filePointer = open("/proc/stb/info/vumodel")
		success = True
	except:
		try:
			filePointer = open("/proc/stb/info/model")
			success = True
		except:
			try:
				filePointer = open("/hdd/model")
				success = True
			except:
				pass

	manu = "unknown"
	model = "unkown"

	if success:
		box = filePointer.readline().strip()
		filePointer.close()

		if box == "ufs910":
			manu = "Kathrein"
			model = "UFS-910"
		elif box == "ufs912":
			manu = "Kathrein"
			model = "UFS-912"
		elif box == "ufs922":
			manu = "Kathrein"
			model = "UFS-922"
		elif box == "solo":
			manu = "VU+"
			model = "Solo"
		elif box == "duo":
			manu = "VU+"
			model = "Duo"
		elif box == "solo2":
			manu = "VU+"
			model = "Solo2"
		elif box == "duo2":
			manu = "VU+"
			model = "Duo2"
		elif box == "uno":
			manu = "VU+"
			model = "Uno"
		elif box == "ultimo":
			manu = "VU+"
			model = "Ultimo"
		elif box == "tf7700hdpvr":
			manu = "Topfield"
			model = "HDPVR-7700"
		elif box == "dm800":
			manu = "Dreambox"
			model = "800"
		elif box == "dm800se":
			manu = "Dreambox"
			model = "800se"
		elif box == "dm7080":
			manu = "Dreambox"
			model = "7080"
		elif box == "dm8000":
			manu = "Dreambox"
			model = "8000"
		elif box == "dm500hd":
			manu = "Dreambox"
			model = "500hd"
		elif box == "dm7025":
			manu = "Dreambox"
			model = "7025"
		elif box == "dm7020hd":
			manu = "Dreambox"
			model = "7020hd"
		elif box == "elite":
			manu = "Azbox"
			model = "Elite"
		elif box == "premium":
			manu = "Azbox"
			model = "Premium"
		elif box == "premium+":
			manu = "Azbox"
			model = "Premium+"
		elif box == "cuberevo-mini":
			manu = "Cubarevo"
			model = "Mini"
		elif box == "hdbox":
			manu = "Fortis"
			model = "HdBox"
		elif box == "gbquad":
			manu = "Gigablue"
			model = "Quad"
		elif box == "gbquadplus":
			manu = "Gigablue"
			model = "QuadPlus"
		elif box == "gb800seplus":
			manu = "Gigablue"
			model = "800SEPlus"
		elif box == "gb800ueplus":
			manu = "Gigablue"
			model = "800UEPlus"
		elif box == "et8000":
			manu = "Xtrend"
			model = "8000"
		elif box == "et10000":
			manu = "Xtrend"
			model = "10000"
		elif box == "maram9":
			manu = "Odin"
			model = "M9"
		else:
			printl2("Unknown box: " + str(box), "__common__::_setBoxtype", "D")

	# set arch for later processing
	getBoxArch()

	# set oe version
	getOeVersion()

	global g_boxData
	g_boxData = (manu, model, g_archType, g_oeVersion)

	printl2("", "__common__::_setBoxtype", "C")

#===========================================================================
#
#===========================================================================
def getBoxArch():
	printl2("", "__common__::setBoxArch", "S")

	if g_archType is None:
		setBoxArch()

	printl2("", "__common__::setBoxArch", "C")
	return g_archType

#===========================================================================
#
#===========================================================================
def setBoxArch():
	printl2("", "__common__::setBoxArch", "S")

	archType = "unknown"

	if (2, 6, 8) > sys.version_info > (2, 6, 6):
		archType = "mipsel"

	elif (2, 7, 4) > sys.version_info > (2, 7, 0):
		archType = "mips32el"

	global g_archType
	g_archType = archType

	printl2("", "__common__::setBoxArch", "C")

#===============================================================================
#
#===============================================================================
def getOeVersion():
	printl2("", "__common__::getOeVersion", "S")

	if g_oeVersion is None:
		setOeVersion()

	printl2("", "__common__::getOeVersion", "C")
	return g_oeVersion

#===============================================================================
#
#===============================================================================
def  setOeVersion():
	printl2("", "__common__::getBoxArch", "S")

	oeVersion = "unknown"

	if (2, 6, 8) > sys.version_info > (2, 6, 6):
		oeVersion = "oe16"

	if (2, 7, 4) > sys.version_info > (2, 7, 0):
		oeVersion = "oe20"

		# check for new oe2.2
		try:
			from enigma import eMediaDatabase
			oeVersion = "oe22"
		except:
			pass

	global g_oeVersion
	g_oeVersion = oeVersion

	printl2("", "__common__::getBoxArch", "C")

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

		try:
			printl2("xml file not found, generating ...", "__common__::checkXmlFile", "D")
			with open(location, "a") as writefile:
				writefile.write("<xml></xml>")
				printl2("writing xml file done", "__common__::checkXmlFile", "D")

		except IOError:
			printl2("io error writing xml", "__common__::checkXmlFile", "D")

		except Exception, e:
			printl2("unknow error writing xml: " + str(e), "__common__::checkXmlFile", "D")

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
def durationToTime(duration):
	printl2("", "__common__::durationToTime", "S")

	m, s = divmod(int(duration)/1000, 60)
	h, m = divmod(m, 60)

	printl2("", "__common__::durationToTime", "C")
	return "%d:%02d:%02d" % (h, m, s)

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
def isValidSize(size):
	printl2("", "__common__::isValidSize", "S")
	valid = False
	result = size / 16
	if size % 16 == 0:
		valid = True

	printl2("", "__common__::isValidSize", "C")
	return valid, result

#===========================================================================
#
#===========================================================================
def saveLiveTv(currentService):
	printl2("", "__common__::saveLiveTv", "S")

	global liveTv

	if liveTv is None:
		liveTv = currentService

	printl2("", "__common__::saveLiveTv", "C")

#===========================================================================
#
#===========================================================================
def getLiveTv():
	printl2("", "__common__::restoreLiveTv", "S")

	printl2("liveTv: " + str(liveTv), "__common__::restoreLiveTv", "D")

	printl2("", "__common__::restoreLiveTv", "C")
	return liveTv

#===========================================================================
#
#===========================================================================
def addNewScreen(screen):
	printl2("", "__common__::addNewScreen", "S")

	screens.append(screen)

	printl2("", "__common__::addNewScreen", "C")

#===========================================================================
#
#===========================================================================
def closePlugin(session):
	printl2("", "__common__::closePlugin", "S")

	for screen in screens:
		try:
			screen.close()
		except Exception:
			# TODO check for memory usage if we are really free after close
			# this could take place if the screen was closed already manually
			pass
		finally:
			session.nav.playService(getLiveTv())

	printl2("", "__common__::closePlugin", "C")

#===========================================================================
#
#===========================================================================
def getPlexHeader(g_sessionID, asDict = True):
	printl2("", "__common__::getPlexHeader", "S")

	boxData = getBoxInformation()
	boxName = config.plugins.dreamplex.boxName.value

	# why do we use ios!!!!! instead of enigma
	# Unable to find client profile for device; platform=Enigma, platformVersion=oe20, device=Dreambox, model=500hd
	# ERROR - [TranscodeUniversalRequest] Unable to find a matching profile

	if asDict:
		plexHeader={'X-Plex-Platform': "iOS",
					'X-Plex-Platform-Version': boxData[3],
					'X-Plex-Provides': "player",
					'X-Plex-Product': "DreamPlex",
					'X-Plex-Version': getVersion(),
					'X-Plex-Device': boxData[0],
					'X-Plex-Device-Name': boxName,
					'X-Plex-Model': boxData[1],
					'X-Plex-Client-Identifier': g_sessionID,
					'X-Plex-Client-Platform': "iOS"}
	else:
		plexHeader = []
		plexHeader.append('X-Plex-Platform:iOS')# + boxData[2]) # arch
		plexHeader.append('X-Plex-Platform-Version:' + boxData[3]) # version
		plexHeader.append('X-Plex-Provides:player')
		plexHeader.append('X-Plex-Product:DreamPlex')
		plexHeader.append('X-Plex-Version:' + getVersion())
		plexHeader.append('X-Plex-Device:' +  boxData[0]) # manu
		plexHeader.append("X-Plex-Device-Name:" + boxName)
		plexHeader.append("X-Plex-Model:" + boxData[1]) # model
		plexHeader.append('X-Plex-Client-Identifier:' + g_sessionID)
		plexHeader.append("X-Plex-Client-Platform:iOS")

	printl2("", "__common__::getPlexHeader", "C")
	return plexHeader

#===========================================================================
#
#===========================================================================
def getUserAgentHeader(asDict = True):
	printl2("", "__common__::getUserAgentHeader", "S")

	if asDict:
		#Create the standard header structure and load with a User Agent to ensure we get back a response.
		header = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',}
	else:
		header = []
		header.append('User-Agent: Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US;rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')

	printl2("", "__common__::getUserAgentHeader", "C")
	return header

#===========================================================================
#
#===========================================================================
def encodeThat(stringToEncode):
	#printl2("", "__common__::encodeThat", "S")
	try:
		encodedString = stringToEncode.encode('utf-8', "ignore")
	except:
		encodedString = stringToEncode

	#printl2("", "__common__::encodeThat", "C")
	return encodedString

#===========================================================================
#
#===========================================================================
def getMyIp():
	#printl2("", "__common__::getMyIp", "S")
	import socket

	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('google.com', 0))
		myIp = s.getsockname()[0]

		#printl2("", "__common__::getMyIp", "S")
		return str(myIp)
	except Exception:
		#printl2("", "__common__::getMyIp", "S")
		return False

#===========================================================================
#
#===========================================================================
def timeToMillis(time):
	return (time['hours']*3600 + time['minutes']*60 + time['seconds'])*1000 + time['milliseconds']

#===========================================================================
#
#===========================================================================
def millisToTime(t):
	millis = int(t)
	seconds = millis / 1000
	minutes = seconds / 60
	hours = minutes / 60
	seconds %= 60
	minutes %= 60
	millis %= 1000
	return {'hours':hours,'minutes':minutes,'seconds':seconds,'milliseconds':millis}

#===========================================================================
#
#===========================================================================
def getXMLHeader():
	#printl("", "getXMLHeader", "S")

	#printl("", "getXMLHeader", "C")
	return '<?xml version="1.0" encoding="utf-8"?>'+"\r\n"

#===========================================================================
#
#===========================================================================
def getOKMsg():
	#printl("", "getOKMsg", "S")

	#printl("", "getOKMsg", "C")
	return getXMLHeader() + '<Response code="200" status="OK" />'

#===========================================================================
#
#===========================================================================
def getPlexHeaders():
	#printl("", "getPlexHeaders", "S")

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

	#printl("", "getPlexHeaders", "C")
	return plexHeader