# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------------
#IMPORT
#------------------------------------------------------------------------------------------
from Plugins.Plugin import PluginDescriptor

#===============================================================================
# main
# Actions to take place when starting the plugin over extensions
#===============================================================================
def main(session, **kwargs):
	session.open(DPS_MainMenu)
	
def DPS_MainMenu(*args, **kwargs):
	import DP_MainMenu
	return DP_MainMenu.DPS_MainMenu(*args, **kwargs)

#===============================================================================
# plugins
# Actions to take place in Plugins
#===============================================================================
def Plugins(**kwargs):
	return [PluginDescriptor(name = "DreamPlex", description = "Plex Client for Enigma2", where = PluginDescriptor.WHERE_PLUGINMENU, icon = "pluginLogo.png", fnc=main)]