# -*- coding: utf-8 -*-
#===============================================================================
# IMPORT
#===============================================================================
from Plugins.Plugin import PluginDescriptor

from Components.config import config, configfile

from DPH_Singleton import Singleton

from __init__ import prepareEnvironment, _ # _ is translation

#===============================================================================
# main
# Actions to take place when starting the plugin over extensions
#===============================================================================
#noinspection PyUnusedLocal
def main(session, **kwargs):
	session.open(DPS_MainMenu)
	
def DPS_MainMenu(*args, **kwargs):
	import DP_MainMenu
	return DP_MainMenu.DPS_MainMenu(*args, **kwargs)

#noinspection PyUnusedLocal
def menu_dreamplex(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("DreamPlex"), main, "dreamplex", 47)]
	return []

#noinspection PyUnusedLocal
def Autostart(reason, session=None, **kwargs):
	if reason == 0:
		prepareEnvironment()
	else:
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()

#===============================================================================
# plugins
# Actions to take place in Plugins
#===============================================================================
#noinspection PyUnusedLocal
def Plugins(**kwargs):
	myList = [PluginDescriptor(name = "DreamPlex", description = "plex client for enigma2", where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "pluginLogo.png", fnc=main),
			PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = Autostart)]
		
	if config.plugins.dreamplex.showInMainMenu.value:
		myList.append(PluginDescriptor(name="DreamPlex", description=_("plex client for enigma2"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_dreamplex))

	return myList