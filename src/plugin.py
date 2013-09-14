# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------------
#IMPORT
#------------------------------------------------------------------------------------------
from Plugins.Plugin import PluginDescriptor
from Components.config import config

#===============================================================================
# main
# Actions to take place when starting the plugin over extensions
#===============================================================================
def main(session, **kwargs):
	session.open(DPS_MainMenu)
	
def DPS_MainMenu(*args, **kwargs):
	import DP_MainMenu
	from __init__ import prepareEnvironment
	prepareEnvironment()
	return DP_MainMenu.DPS_MainMenu(*args, **kwargs)

def menu_dreamplex(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("DreamPlex"), main, "dreamplex", 47)]
	return []

#===============================================================================
# plugins
# Actions to take place in Plugins
#===============================================================================
def Plugins(**kwargs):
	list = [PluginDescriptor(name = "DreamPlex", description = "plex client for enigma2", where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "pluginLogo.png", fnc=main)]
		
	if config.plugins.dreamplex.showInMainMenu.value == True:
		list.append(PluginDescriptor(name="DreamPlex", description=_("plex client for enigma2"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_dreamplex))

	return list