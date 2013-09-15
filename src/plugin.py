# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------------------
#IMPORT
#------------------------------------------------------------------------------------------
from Plugins.Plugin import PluginDescriptor
from Components.config import config
from __init__ import prepareEnvironment

#===============================================================================
# main
# Actions to take place when starting the plugin over extensions
#===============================================================================
def main(session, **kwargs):
	session.open(DPS_MainMenu)
	
def DPS_MainMenu(*args, **kwargs):
	import DP_MainMenu
	return DP_MainMenu.DPS_MainMenu(*args, **kwargs)

def menu_dreamplex(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("DreamPlex"), main, "dreamplex", 47)]
	return []

def Autostart(reason, session=None, **kwargs):
	if reason == 0:
		prepareEnvironment()
	else:
		config.plugins.dreamplex.save()

#===============================================================================
# plugins
# Actions to take place in Plugins
#===============================================================================
def Plugins(**kwargs):
	list = [PluginDescriptor(name = "DreamPlex", description = "plex client for enigma2", where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "pluginLogo.png", fnc=main),
			PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = Autostart)]
		
	if config.plugins.dreamplex.showInMainMenu.value == True:
		list.append(PluginDescriptor(name="DreamPlex", description=_("plex client for enigma2"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_dreamplex))

	return list