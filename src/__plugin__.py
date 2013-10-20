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
from __common__ import printl2 as printl

#===============================================================================
# GLOBAL
#===============================================================================
gPlugins = []

#===============================================================================
# 
#===============================================================================
def registerPlugin(plugin):
	printl("", "__plugin__::registerPlugin", "S")
	
	ps = []
	if type(plugin) is list:
		ps = plugin
	else:
		ps.append(plugin)
	for p in ps:
		if p not in gPlugins:
			printl("registered: name=" + str(p.name) + " where=" + str(p.where), "__plugin__::registerPlugin", "D")
			gPlugins.append(p)
	
	printl("", "__plugin__::registerPlugin", "C")

#===============================================================================
# 
#===============================================================================
def getPlugins(where=None):
	printl("", "__plugin__::getPlugins", "S")
	
	if where is None:
		printl("", "__plugin__::getPlugins", "C")
		return gPlugins
	else:
		plist = []
		for plugin in gPlugins:
			if plugin.where == where:
				plist.append(plugin)
		
		plist.sort(key=lambda x: x.weight)
		printl(str(plist), "__plugin__::getPlugins", "D")
		
		printl("", "__plugin__::getPlugins", "C")
		return plist
	
#===============================================================================
# 
#===============================================================================
def getPlugin(pid, where):
	printl("", "__plugin__::getPlugin", "S")
	
	for plugin in gPlugins:
		if plugin.pid == pid and plugin.where == where:
			
			printl("plugin found ... " + str(plugin), "__plugin__::getPlugin", "D")
			printl("", "__plugin__::getPlugin", "C")
			return plugin
	
	printl("", "__plugin__::getPlugin", "C")
	return None

#===============================================================================
# 
#===============================================================================
class Plugin(object):
	MENU_SERVER = 0
	MENU_MAIN = 1
	MENU_PICTURES = 2
	MENU_MUSIC = 3
	MENU_VIDEOS = 4
	MENU_MOVIES = 5
	MENU_TVSHOWS = 6
	MENU_PROGRAMS = 7
	MENU_SYSTEM = 8
	AUTOSTART = 9

	SETTINGS = 10

	MENU_MOVIES_PLUGINS = 11
	AUTOSTART_E2 = 12
	STOP_E2 = 13
	MENU_DEV = 14

	WAKEUP = 15
	AUTOSTART_DELAYED = 16
	MENU_FILTER = 17
	MENU_ABOUT = 18
	MENU_HELP = 19
	MENU_CHANNELS = 20

	INFO_PLAYBACK = 100
	#INFO_SEEN = 101

	pid = None
	name = None
	desc = None
	start = None
	fnc = None
	where = None
	weight = 100
	supportStillPicture = False

	#===========================================================================
	# 
	#===========================================================================
	def __init__(self, pid, name=None, desc=None, start=None, fnc=None, where=None, supportStillPicture=False, weight=100):
		printl("", self, "S")

		self.pid = pid
		self.name = name
		if desc is None:
			self.desc = self.name
		else:
			self.desc = desc
		self.start = start
		self.fnc = fnc
		self.where = where
		self.weight = weight
		self.supportStillPicture = supportStillPicture

		printl("", self, "C")
