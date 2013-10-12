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

	if libraryName == "movies" or libraryName == "tvshows":
		availableViewList = getViewsFromSkinParams("cineView")
	
	elif libraryName == "music":
		availableViewList = getViewsFromSkinParams("musicView")
	
	else:
		availableViewList = ()

	printl("", __name__, "C")
	return availableViewList

#===========================================================================
# 
#===========================================================================
def getViewsFromSkinParams(type):
	printl("", __name__, "S")
	
	tree = Singleton().getSkinParamsInstance()
	#tree = getXmlContent("/usr/lib/enigma2/python/Plugins/Extensions/DreamPlex/skins/" + config.plugins.dreamplex.skins.value +"/params")
	
	availableViewList = []
	
	if type == "cineView":
		myFile = "DP_ViewCine"
		myClass = "DPS_ViewCine"
		defaultParams = getCineViewDefaults()
	
	elif type == "musicView":
		myFile = "DP_ViewMusic"
		myClass = "DPS_ViewMusic"
		defaultParams = getMusicViewDefaults()
		
	else:
		pass
	
	for view in tree.findall(type):
		name = str(view.get('name'))
		currentParams = {}
		
		for param in defaultParams:
			#check if there are params that we have to override
			value = view.get(param, None)
			printl("value: " + str(value), __name__, "D")
			# check if this value is mandatory
			# if we are mandatory we stop here
			if defaultParams[param] == "mandatory" and value is None:
				assert()
				
			# if there is one we overwrite the default value
			if value is not None:
				
				# translate xml value to real true or false
				if value == "true" or value == "True":
					value = True
				
				if value == "false" or value == "False":
					value = False
				
			else:
				# fill not existing params with default values
				value = defaultParams[param]
				
			currentParams[param] = value
		
		printl("currentParams: " + str(currentParams),__name__, "D")
		view = (_(name), myFile, myClass, currentParams)
		
		availableViewList.append(view)
	
	printl("availableViewList: " + str(availableViewList), __name__, "D")
	printl("", __name__, "C")
	return availableViewList

#===========================================================================
# 
#===========================================================================
def getCineViewDefaults():
	printl("", __name__, "S")
	
	defaults = {}
	# mandatory items have to be defined or a assert error will come
	defaults["itemsPerPage"]		= "mandatory"
	defaults["apiLevel"]			= "mandatory"
	defaults["screen"]				= "mandatory"
	
	defaults["backdropHeight"]		= "315"
	defaults["backdropWidth"]		= "560"
	defaults["posterHeight"]		= "268"
	defaults["posterWidth"]			= "195"
	defaults["current"]				= True
	defaults["total"]				= True
	defaults["functionsContainer"]	= True
	defaults["showBackdrop"]		= True
	defaults["showPoster"]			= True
	defaults["audio"] 				= True
	defaults["resolution"] 			= True
	defaults["aspect"] 				= True
	defaults["codec"] 				= True
	defaults["rated"] 				= True
	defaults["title"] 				= True
	defaults["tag"] 				= True
	defaults["shortDescription"] 	= True
	defaults["subtitles"] 			= True
	defaults["selectedAudio"] 		= True
	defaults["genre"] 				= True
	defaults["year"] 				= True
	defaults["runtime"] 			= True
	defaults["backdroptext"]		= True
	defaults["postertext"]			= True
	defaults["rating_stars"] 		= True
	
	printl("", __name__, "C")
	return defaults

#===========================================================================
# 
#===========================================================================
def getMusicViewDefaults():
	printl("", __name__, "S")
	
	defaults = {}
	# mandatory items have to be defined or a assert error will come
	defaults["itemsPerPage"]		= "mandatory"
	defaults["apiLevel"]			= "mandatory"
	defaults["screen"]				= "mandatory"

	defaults["current"]				= True
	defaults["total"]				= True
	defaults["functionsContainer"]	= True
	defaults["showBackdrop"]		= True
	defaults["showPoster"]			= True
	defaults["audio"] 				= True
	defaults["resolution"] 			= True
	defaults["aspect"] 				= True
	defaults["codec"] 				= True
	defaults["rated"] 				= True
	defaults["title"] 				= True
	defaults["tag"] 				= True
	defaults["shortDescription"] 	= True
	defaults["subtitles"] 			= True
	defaults["selectedAudio"] 		= True
	defaults["genre"] 				= True
	defaults["year"] 				= True
	defaults["runtime"] 			= True
	defaults["backdroptext"]		= True
	defaults["postertext"]			= True
	defaults["rating_stars"] 		= True
	
	printl("", __name__, "C")
	return defaults
	