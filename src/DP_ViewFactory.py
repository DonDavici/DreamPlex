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
import copy

from DPH_Singleton import Singleton

from __common__ import printl2 as printl
from __init__ import _ # _ is translation


#===========================================================================
#
#===========================================================================
def getDefaultCineElementsList():
	printl("", __name__, "S")

	elementsList = ["pagination", "total", "backdrop", "poster", "writer", "resolution", "season", "cast", "audio", "info",
	                "aspect", "codec", "rated", "title", "grandparentTitle" ,"tag", "shortDescription", "subtitles", "director",
	                "genre", "year", "runtime", "backdroptext", "postertext", "rating_stars", "sound", "filter", "pagination", "total",
	                "btn_red", "btn_green", "btn_yellow", "btn_blue"]

	printl("", __name__, "C")
	return elementsList

#===========================================================================
#
#===========================================================================
def getDefaultSettingsList():
	printl("", __name__, "S")

	settingsList = ["itemsPerPage", "apiLevel", "screen", "backdropVideos", "name"]

	printl("", __name__, "C")
	return settingsList

#===============================================================================
# 
#===============================================================================
def getViews(libraryName):
	"""
	@return: availableViewList
	"""
	printl("", "DP_View::getViews", "S")

	if libraryName == "movies":
		availableViewList = getViewsFromSkinParams("movieView")

	elif libraryName == "shows":
		availableViewList = getViewsFromSkinParams("showView")

	elif libraryName == "music":
		availableViewList = getViewsFromSkinParams("musicView")
	
	else:
		availableViewList = ()

	printl("", __name__, "C")
	return availableViewList

#===========================================================================
# 
#===========================================================================
def getViewsFromSkinParams(myType):
	printl("", __name__, "S")
	
	tree = Singleton().getSkinParamsInstance()

	availableViewList = []

	if myType == "movieView":
		myFile = "DP_ViewMovies"
		myClass = "DPS_ViewMovies"
		defaultParams = getMovieViewDefaults()

	elif myType == "showView":
		myFile = "DP_ViewShows"
		myClass = "DPS_ViewShows"
		defaultParams = getShowViewDefaults()

	elif myType == "musicView":
		myFile = "DP_ViewMusic"
		myClass = "DPS_ViewMusic"
		defaultParams = getMusicViewDefaults()
		
	else:
		raise Exception()

	for view in tree.findall(myType):
		# lets copy params to new alterable variable
		currentParams = copy.deepcopy(defaultParams)
		printl("currentParams: " + str(currentParams), __name__, "D")

		useMe, subViewDict = getSubViewParams(view)
		if useMe:
			currentParams["subViews"] = subViewDict

		name = str(view.get("name"))
		printl("viewMe:" + str(view), __name__, "D")

		# settings
		settings = defaultParams["settings"]
		for setting in settings:
			printl("setting:" + str(setting), __name__, "D")
			#check if there are params that we have to override
			value = view.get(setting, None)
			printl("value: " + str(value), __name__, "D")

			# check if this value is mandatory
			# if we are mandatory we stop here
			if defaultParams["settings"][setting] == "mandatory" and value is None:
				raise Exception
			else:
				currentParams["settings"][setting] = translateValues(value)

		# override params in the main first = main screen
		for main in view.findall("main"):
			name = main.get("name")
			printl("name: " + str(name), __name__, "D")

			params = main.attrib
			printl("params: " + str(params), __name__, "D")

			for key, value in params.items():
				translatedValue = translateValues(value)

				if key != "name":
					currentParams["elements"][name][key] = translatedValue

		view = (_(name), myFile, myClass, currentParams)
		
		availableViewList.append(view)
	
	printl("availableViewList: " + str(availableViewList), __name__, "D")
	printl("", __name__, "C")
	return availableViewList

#===========================================================================
#
#===========================================================================
def getSubViewParams(tree):
	printl("", __name__, "S")

	useMe = False
	myDict = {}

	for view in tree.findall("subView"):
		useMe = True
		subViewName = view.get("name", None)
		myDictParams = {}

		if subViewName is not None: # we do this for compatibility with oe16 with python 2.7
			for element in view.iter("element"):
				name = element.get("name")
				myDictParams[name] = {}

				params = element.attrib
				printl("params: " + str(params), __name__, "D")

				for key, value in params.items():
					translatedValue = translateValues(value)

					if key != "name":
						myDictParams[name][key] = translatedValue

		myDict[subViewName] = myDictParams

	printl("", __name__, "C")
	return useMe, myDict

#===========================================================================
# 
#===========================================================================
def getMovieViewDefaults():
	printl("", __name__, "S")
	params = {}

	params["settings"] = {}
	settingsList = getDefaultSettingsList()
	# mandatory items have to be defined or a assert error will come
	for setting in settingsList:
		params["settings"][setting] = "mandatory"

	params["elements"] = {}
	elementsList = getDefaultCineElementsList()

	# init elements
	for element in elementsList:
		params["elements"][element] = {}
		params["elements"][element]["visible"] = True

	# override default True
	params["elements"]["grandparentTitle"]["visible"]              = False
	params["elements"]["season"]["visible"]                        = False
	params["elements"]["writer"]["visible"]                        = False
	params["elements"]["director"]["visible"]                      = False
	params["elements"]["cast"]["visible"]                          = False

	# add addional params in elements
	params["elements"]["backdrop"]["height"]                       = "315"
	params["elements"]["backdrop"]["width"]                        = "560"
	params["elements"]["backdrop"]["postfix"]                      = "_backdrop.jpg"

	params["elements"]["poster"]["height"]                         = "268"
	params["elements"]["poster"]["width"]                          = "195"
	params["elements"]["poster"]["postfix"]                        = "_poster.jpg"

	printl("", __name__, "C")
	return params

#===========================================================================
#
#===========================================================================
def getShowViewDefaults():
	printl("", __name__, "S")
	params = {}

	params["settings"] = {}
	settingsList = getDefaultSettingsList()
	# mandatory items have to be defined or a assert error will come
	for setting in settingsList:
		params["settings"][setting] = "mandatory"

	params["elements"] = {}
	elementsList = getDefaultCineElementsList()

	# init elements
	for element in elementsList:
		params["elements"][element] = {}
		params["elements"][element]["visible"] = True

	# override default True
	params["elements"]["subtitles"]["visible"]                     = False
	params["elements"]["audio"]["visible"]                         = False
	params["elements"]["runtime"]["visible"]                       = False
	params["elements"]["season"]["visible"]                        = False
	params["elements"]["director"]["visible"]                      = False
	params["elements"]["cast"]["visible"]                          = False
	params["elements"]["writer"]["visible"]                        = False
	params["elements"]["season"]["visible"]                        = False

	# add addional params in elements
	params["elements"]["backdrop"]["height"]                       = "315"
	params["elements"]["backdrop"]["width"]                        = "560"
	params["elements"]["backdrop"]["postfix"]                      = "_backdrop.jpg"

	params["elements"]["poster"]["height"]                         = "268"
	params["elements"]["poster"]["width"]                          = "195"
	params["elements"]["poster"]["postfix"]                        = "_poster.jpg"

	printl("", __name__, "C")
	return params

#===========================================================================
# 
#===========================================================================
def getMusicViewDefaults():
	printl("", __name__, "S")
	params = {}

	params["settings"] = {}
	settingsList = getDefaultSettingsList()
	# mandatory items have to be defined or a assert error will come
	for setting in settingsList:
		params["settings"][setting] = "mandatory"

	params["elements"] = {}
	elementsList = getDefaultCineElementsList()

	# init elements
	for element in elementsList:
		params["elements"][element] = {}
		params["elements"][element]["visible"] = True

	# override default True
	params["elements"]["subtitles"]["visible"]                     = False
	params["elements"]["audio"]["visible"]                         = False
	params["elements"]["year"]["visible"]                          = False
	params["elements"]["runtime"]["visible"]                       = False
	params["elements"]["season"]["visible"]                        = False
	params["elements"]["writer"]["visible"]                        = False
	params["elements"]["director"]["visible"]                      = False
	params["elements"]["cast"]["visible"]                          = False
	params["elements"]["btn_yellow"]["visible"]                    = False

	# add addional params in elements
	params["elements"]["backdrop"]["height"]                       = "315"
	params["elements"]["backdrop"]["width"]                        = "560"
	params["elements"]["backdrop"]["postfix"]                      = "_backdrop.jpg"

	params["elements"]["poster"]["height"]                         = "268"
	params["elements"]["poster"]["width"]                          = "195"
	params["elements"]["poster"]["postfix"]                        = "_poster.jpg"

	printl("", __name__, "C")
	return params

#===========================================================================
#
#===========================================================================
def translateValues(value):
	printl("", __name__, "S")

	# translate xml value to real true or false
	if value == "true" or value == "True":
		value = True

	if value == "false" or value == "False":
		value = False

	printl("", __name__, "C")
	return value

#===========================================================================
#
#===========================================================================
def getGuiElements():
	printl("", __name__, "S")

	tree = Singleton().getSkinParamsInstance()

	guiElements = {}
	for guiElement in tree.findall('guiElement'):
		name = str(guiElement.get('name'))
		path = str(guiElement.get('path'))
		guiElements[name] = path

	printl("guiElements: " + str(guiElements), __name__, "D")
	printl("", __name__, "C")
	return guiElements