# -*- coding: utf-8 -*-
'''
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
'''
#===============================================================================
# IMPORT
#===============================================================================
import sys
import os
import datetime

from enigma import getDesktop, addFont
from skin import loadSkin
from Components.config import config
from Components.AVSwitch import AVSwitch

from DPH_Singleton import Singleton

#===============================================================================
# GLOBAL
#===============================================================================
gConnectivity = None
gLogFile = None
gBoxType = None

# ****************************** VERBOSITY Level *******************************
VERB_ERROR       = 0  # "E" shows error
VERB_INFORMATION = 0  # "I" shows important highlights to have better overview if something really happening or not

VERB_WARNING     = 1  # "W" shows warning

VERB_DEBUG 		 = 2  # "D" shows additional debug information

VERB_STARTING    = 3  # "S" shows started functions/classes etc.
VERB_CLOSING     = 3  # "C" shows closing functions/classes etc.

VERB_EXTENDED	 = 4  # "X" shows information that are not really needed at all can only be activated by hand

STARTING_MESSAGE = ">>>>>>>>>>"
CLOSING_MESSAGE =  "<<<<<<<<<<"

#===============================================================================
# 
#===============================================================================
def printl2 (string, parent=None, dmode= "U", obfuscate = False, steps = 4):
	'''
	ConfigSelection(default="0", choices = [("0", _("Silent")),("1", _("Normal")),("2", _("High")),("3", _("All"))])
	
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
	'''

	debugMode = int(config.plugins.dreamplex.debugMode.value)
	
	
	#TODO change before making new version
	#debugMode = 2 
	
	out = ""
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
			out = str(classname) + str(sys._getframe(1).f_code.co_name) +" -> " + str(string)
		else:
			classname = ""
			out = str(parent) + " -> " + str(string)

	if dmode == "E" :
		verbLevel = VERB_ERROR
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "E" + "  " + str(out)
			writeToLog(dmode, out)
	
	elif dmode == "W":
		verbLevel = VERB_WARNING
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "W" + "  " + str(out)
			writeToLog(dmode, out)
	
	elif dmode == "I":
		verbLevel = VERB_INFORMATION
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "I" + "  " + str(out)
			writeToLog(dmode, out)
	
	elif dmode == "D":
		verbLevel = VERB_DEBUG
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "D" + "  " + str(out)	
			writeToLog(dmode, out)
	
	elif dmode == "S":
		verbLevel = VERB_STARTING
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "S" + "  " + str(out) + STARTING_MESSAGE
			writeToLog(dmode, out + STARTING_MESSAGE)
	
	elif dmode == "C":
		verbLevel = VERB_CLOSING
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "C" + "  " + str(out) +  CLOSING_MESSAGE
			writeToLog(dmode, out +  CLOSING_MESSAGE)
	
	elif dmode == "U":
		print "[DreamPlex] " + "U  specify me!!!!!" + "  " + str(out)
		writeToLog(dmode, out)
		
	elif dmode == "X":
		verbLevel = VERB_EXTENDED
		if verbLevel <= debugMode:
			print "[DreamPlex] " + "D" + "  " + str(out)	
			writeToLog(dmode, out)
		
	else:
		print "[DreamPlex] " + "OLD CHARACTER CHANGE ME !!!!!" + "  " + str(out)
	


#===============================================================================
# 
#===============================================================================
def writeToLog(dmode, out):
	'''
	singleton handler for the log file
	
	@param dmode: E, W, S, H, A, C, I
	@param out: message string
	@return: none
	'''
	try:
		#=======================================================================
		# if gLogFile is None:
		#	openLogFile()
		#=======================================================================
		instance = Singleton()
		if instance.getLogFileInstance() is "":
			openLogFile()
			gLogFile = instance.getLogFileInstance()
			gLogFile.truncate()
		else:
			gLogFile = instance.getLogFileInstance()
			
		now = datetime.datetime.now()
		gLogFile.write("%02d:%02d:%02d.%07d " % (now.hour, now.minute, now.second, now.microsecond) + " >>> " + str(dmode) + " <<<  " + str(out) + "\n")
		gLogFile.flush()
	
	except Exception, ex:
		printl2("Exception(" + str(type(ex)) + "): " + str(ex), "__common__::writeToLog", "E")


#===============================================================================
# 
#===============================================================================
def openLogFile():
	'''
	singleton instance for logfile
	
	@param: none
	@return: none
	'''
	#printl2("", "openLogFile", "S")
	
	logDir = config.plugins.dreamplex.logfolderpath.value
	
	now = datetime.datetime.now()
	try:
		instance = Singleton()
		instance.getLogFileInstance(open(logDir + "dreamplex.log", "w"))
		
	except Exception, ex:
		printl2("Exception(" + str(type(ex)) + "): " + str(ex), "openLogFile", "E")
	
	#printl2("", "openLogFile", "C")

#===============================================================================
# 
#===============================================================================
def testInetConnectivity(target = "http://www.google.com"):
	'''
	test if we get an answer from the specified url
	
	@param url:
	@return: bool
	'''
	printl2("", "__common__::testInetConnectivity", "S")
	
	import urllib2
	from   sys import version_info
	import socket
	
	try:
		opener = urllib2.build_opener()
		page = None
		if version_info[1] >= 6:
			page = opener.open(target, timeout=2)
		else:
			socket.setdefaulttimeout(2)
			page = opener.open(target)
		if page is not None:
			
			printl2("","__common__::testInetConnectivity", "C")
			return True
		else:
			
			printl2("","__common__::testInetConnectivity", "C")
			return False
	except:
		
		printl2("", "__common__::testInetConnectivity", "C")
		return False

#===============================================================================
# 
#===============================================================================
def testPlexConnectivity(ip, port):
	'''
	test if the plex server is online on the specified port
	
	@param ip: e.g. 192.168.0.1
	@param port: e.g. 32400
	@return: bool
	'''
	printl2("", "__common__::testPlexConnectivity", "S")
	
	import socket
	
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	printl2("IP => " + str(ip), "__common__::testPlexConnectivity", "I")
	printl2("PORT => " + str(port), "__common__::testPlexConnectivity","I")
	
	try:
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
	'''
	registers fonts for skins
	
	@param: none 
	@return none
	'''
	printl2("", "__common__::registerPlexFonts", "S")
	
	printl2("adding fonts", "__common__::registerPlexFonts", "I")

	addFont("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/mayatypeuitvg.ttf", "Modern", 100, False)
	printl2("added => mayatypeuitvg.ttf", "__common__::registerPlexFonts", "I")
	
	addFont("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/goodtime.ttf", "Named", 100, False)
	printl2("added => goodtime.ttf", "__common__::registerPlexFonts", "I")
	
	addFont("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/saint.ttf", "Saint", 100, False)
	printl2("added => saint.ttf", "__common__::registerPlexFonts", "I")
	
	printl2("", "__common__::registerPlexFonts", "C")

#===============================================================================
# 
#===============================================================================
def loadPlexSkin():
	'''
	loads depending on the desktop size the corresponding skin.xml file
	
	@param: none 
	@return none
	'''
	printl2("", "__common__::loadPlexSkin", "S")
	
	skin = None
	desktop = getDesktop(0).size().width()
	#===========================================================================
	# if desktop == 720:
	#	skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/720x576/skin.xml"
	# elif desktop == 1024:
	#	skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/1024x576/skin.xml"
	# elif desktop == 1280:
	#===========================================================================
	skin = "/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skin/1280x720/skin.xml"
	
	if skin:
		loadSkin(skin)
		
	printl2("", "__common__::loadPlexSkin", "C")
#===============================================================================
# 
#===============================================================================
def checkPlexEnvironment():
	'''
	checks needed file structure for plex
	
	@param: none 
	@return none	
	'''
	printl2("","__common__::checkPlexEnvironment", "S")
	
	playerTempFolder = config.plugins.dreamplex.playerTempPath.value
	logFolder = config.plugins.dreamplex.logfolderpath.value
	mediaFolder = config.plugins.dreamplex.mediafolderpath.value
	
	checkDirectory(playerTempFolder)
	checkDirectory(logFolder)
	checkDirectory(mediaFolder)
	
	printl2("","__common__::checkPlexEnvironment", "C")
	
#===============================================================================
# 
#===============================================================================
def checkDirectory(directory):
	'''
	checks if dir exists. if not it is added
	
	@param directory: e.g. /media/hdd/
	@return: none
	'''
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
	
	printl2("","__common__::checkDirectory", "C")

#===============================================================================
# 
#===============================================================================		
def getServerFromURL(url ): # CHECKED
	'''
	Simply split the URL up and get the server portion, sans port
	
	@param url: with or without protocol
	@return: the server URL
	'''
	printl2("","__common__::getServerFromURL", "S")
	
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
	'''
	'''
	printl2("", "__common__::getBoxtype", "C")
	global gBoxType

	if gBoxType is not None:
		
		printl2("", "__common__::getBoxtype", "C")
		return gBoxType
	else:
		setBoxInformation()
		
		printl2("", "__common__::getBoxtype", "C")
		return gBoxType

#===============================================================================
# 
#===============================================================================
def setBoxInformation():
	'''
	'''
	printl2("", "__common__::_setBoxtype", "C")
	global gBoxType
	
	try:
		file = open("/proc/stb/info/model", "r")
	except:
		file = open("/hdd/model", "r")
	box = file.readline().strip()
	file.close()
	manu = "Unknown"
	model = box #"UNKNOWN" # Fallback to internal string
	arch = "sh4" # "unk" # Its better so set the arch by default to unkown so no wrong update information will be displayed
	version = ""
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
	
	gBoxType = (manu, model, arch, version)
	printl2("", "__common__::_setBoxtype", "C")

#===============================================================================
# 
#===============================================================================
def getBoxArch():
	'''
	'''
	printl2("", "__common__::getBoxArch", "S")
	
	ARCH = "unknown"
   
	if (sys.version_info < (2, 6, 8) and sys.version_info > (2, 6, 6)):
		ARCH = "oe16"
                   
	if (sys.version_info < (2, 7, 4) and sys.version_info > (2, 7, 0)):
		ARCH = "oe20"
			
	printl2("", "__common__::getBoxArch", "C")
	return ARCH

#===============================================================================
# 
#===============================================================================
def findMountPoint(pth):
	'''
	Example: findMountPoint("/media/hdd/some/file") returns "/media/hdd" 
	'''
	printl2("","__common__::findMountPoint", "S")                                    
	
	pth = path.abspath(pth)                                                                                        
	
	while not path.ismount(pth):                                                                                    
		pth = path.dirname(pth)                                                                                
	
	printl2("","__common__::findMountPoint", "C")
	return pth                                                                                                         

#===============================================================================
# 
#===============================================================================
def findSafeRecordPath(dirname):
	'''
	'''  
	printl2("","__common__::findSafeRecordPath", "S")					   
	
	if not dirname:
		printl2("","__common__::findSafeRecordPath", "C")								   
		return None							   
	
	dirname = path.realpath(dirname)			   
	mountpoint = findMountPoint(dirname)	 
	
	if mountpoint in ('/', '/media'):			  
		printl2('media is not mounted:'+ str(dirname), "__common__::findSafeRecordPath", "D")
		
		printl2("","__common__::findSafeRecordPath", "C")
		return None										 
	
	if not path.isdir(dirname):							  
		try:												
			makedirs(dirname)						
		except Exception, ex:							   
			printl2('Failed to create dir "%s":' % str(dirname) + str(ex), "__common__::findSafeRecordPath", "D")
			
			printl2("","__common__::findSafeRecordPath", "C")
			return None												   
	
	printl2("","__common__::findSafeRecordPath", "C")
	return dirname																

#===============================================================================
# 
#===============================================================================
def normpath(path):
	'''
	'''
	printl2("","__common__::normpath", "S")
	
	if path is None:
		printl2("","__common__::normpath", "C")
		return None
	
	path = path.replace("\\","/").replace("//", "/")
	
	if path == "/..":
		printl2("","__common__::normpath", "C")
		return None
	
	if len(path) > 0 and path[0] != '/':
		path = posixpath.normpath('/' + path)[1:]
	else:
		path = posixpath.normpath(path)

	if len(path) == 0 or path == "//":
		printl2("","__common__::normpath", "C")
		return "/"
	
	elif path == ".":
		printl2("","__common__::normpath", "C")
		return None
	
	printl2("","__common__::normpath", "C")
	return path

#===============================================================================
# pretty_time_format
#===============================================================================
def prettyFormatTime(msec):
	'''
	'''
	printl2("","__common__::prettyFormatTime", "S")
	
	seconds = msec / 1000
	hours = seconds // (60*60)
	seconds %= (60*60)
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
		printl2("","__common__::prettyFormatTime", "C")
		return "%i %s %02i %s %02i %s" % (hours, hrstr, minutes, minstr, seconds, secstr)
	
	elif minutes > 0:
		printl2("","__common__::prettyFormatTime", "C")
		return "%i %s %02i %s" % (minutes, minstr, seconds, secstr)
	
	else:
		printl2("","__common__::prettyFormatTime", "C")
		return "%i %s" % (seconds, secstr)

#===============================================================================
# time_format
#===============================================================================
def formatTime(msec):
	'''
	'''
	printl2("","__common__::formatTime", "S")
	
	seconds = msec / 1000
	hours = seconds // (60*60)
	seconds %= (60*60)
	minutes = seconds // 60
	seconds %= 60
	
	if hours > 0:
		printl2("","__common__::formatTime", "C")
		return "%i:%02i:%02i" % (hours, minutes, seconds)
	
	elif minutes > 0:
		printl2("","__common__::formatTime", "C")
		return "%i:%02i" % (minutes, seconds)
	
	else:
		printl2("","__common__::formatTime", "C")
		return "%i" % (seconds)
	
#===============================================================================
# 
#===============================================================================
def getScale():
	'''
	'''
	
	printl2("","__common__::getScale", "S")
	
	return AVSwitch().getFramebufferScale()
	
	printl2("","__common__::getScale", "C")