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
import math
import time

from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Label import Label
from Components.config import config
from Components.config import NumericalTextInput

from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from enigma import eServiceReference
from enigma import loadPNG

from Tools.Directories import fileExists

from urllib import urlencode, quote_plus

from twisted.web.client import downloadPage

from Plugins.Extensions.DreamPlex.DPH_Arts import getPictureData
from Plugins.Extensions.DreamPlex.DP_Player import DP_Player
from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton
from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl, getXmlContent, convertSize
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugins, Plugin

#===============================================================================
# 
#===============================================================================
def getViews(libraryName):
	'''
	@param: none 
	@return: availableViewList
	'''
	printl("", "DP_View::getViews", "S")
	
	multiView = True
	
	if multiView:
		if libraryName == "movies":
			availableViewList = getViewsFromSkinParams("movieView")
		
		elif libraryName == "tvshows":
			availableViewList = getViewsFromSkinParams("showView")
		
		elif libraryName == "music":
			availableViewList = getViewsFromSkinParams("musicView")
		
		else:
			availableViewList = ()
		
	else:
		availableViewList = []
		
		if libraryName == "movies" or libraryName == "tvshows":
			viewList = (
				(_("Short List"), "DP_ViewList", "DPS_ViewList"),
				(_("Long List"), "DP_ViewListLong", "DPS_ViewListLong"), 
				(_("Backdrop"), "DP_ViewBackdrop", "DPS_ViewBackdrop"), 
			)
		elif libraryName == "music":
			viewList = (
						(_("Music"), "DP_ViewMusic", "DPS_ViewMusic"), 
					)
		else:
			viewList = ()
		
		for view in viewList:
			try:
				availableViewList.append(view)
			except Exception, ex:
				printl("View %s not available in this skin" % view[1] + " exception: " + ex , __name__, "W")
	
	printl("", __name__, "C")
	return availableViewList

#===========================================================================
# 
#===========================================================================
def getViewsFromSkinParams(type):
	printl("", __name__, "S")
	
	tree = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
	
	availableViewList = []
	availableParams = ("itemsPerPage", "showPoster", "showBackdrop")
	
	if type == "movieView":
		myFile = "DP_ViewMovie"
		myClass = "DPS_ViewMovie"
	
	elif type == "showView":
		myFile = "DP_ViewShow"
		myClass = "DPS_ViewShow"
		
	elif type == "musicView":
		myFile = "DP_ViewMusic"
		myClass = "DPS_ViewMusic"
		
	else:
		pass
	
	for view in tree.findall(type):
		name = str(view.get('name'))

		params = {}
		for param in availableParams:
			params[param] = str(view.get(param))
		
		printl("params: " + str(params),__name__, "D")
		view = (_(name), myFile, myClass, params)
		
		availableViewList.append(view)
	
	printl("availableViewList: " + str(availableViewList), __name__, "D")
	printl("", __name__, "C")
	return availableViewList