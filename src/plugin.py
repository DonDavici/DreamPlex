# -*- coding: utf-8 -*-
#===============================================================================
# IMPORT
#===============================================================================
from Plugins.Plugin import PluginDescriptor

from Components.config import config, configfile

from __init__ import prepareEnvironment, _ # _ is translation

#===============================================================================
# GLOBALS
#===============================================================================
HttpDeamonThread = None
global_session = None

#===============================================================================
# main
# Actions to take place when starting the plugin over extensions
#===============================================================================
#noinspection PyUnusedLocal
def main(session, **kwargs):
	session.open(DPS_MainMenu)

#===========================================================================
#
#===========================================================================
def DPS_MainMenu(*args, **kwargs):
	import DP_MainMenu
	return DP_MainMenu.DPS_MainMenu(*args, **kwargs)

#===========================================================================
#
#===========================================================================
#noinspection PyUnusedLocal
def menu_dreamplex(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("DreamPlex"), main, "dreamplex", 47)]
	return []

#===========================================================================
#
#===========================================================================
#noinspection PyUnusedLocal
def Autostart(reason, session=None, **kwargs):
	if reason == 0:
		prepareEnvironment()

		if config.plugins.dreamplex.remoteAgent.value:
			startRemoteDeamon()
	else:
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()

		HttpDeamonThread.stopRemoteDeamon()

#===========================================================================
#
#===========================================================================
def startRemoteDeamon():
	from DPH_RemoteListener import HttpDeamon
	global HttpDeamonThread

	# we use the global g_mediaSyncerInfo.instance to take care only having one instance
	HttpDeamonThread = HttpDeamon(config.plugins.dreamplex.remotePort.value)
	HttpDeamonThread.PlayerDataPump.recv_msg.get().append(gotThreadMsg)
	HttpDeamonThread.startDeamon()

#===========================================================================
# msg as second params is needed -. do not remove even if it is not used
# form outside!!!!
#===========================================================================
# noinspection PyUnusedLocal
def gotThreadMsg(msg):
	from DP_Player import startPlayer

	msg = HttpDeamonThread.PlayerData.pop()
	startPlayer(global_session, msg[0])

#===========================================================================
#
#===========================================================================
def sessionStart(reason, session):
	global global_session
	global_session = session

	HttpDeamonThread.setSession(session)

#===============================================================================
# plugins
# Actions to take place in Plugins
#===============================================================================
#noinspection PyUnusedLocal
def Plugins(**kwargs):
	myList = []
	myList.append(PluginDescriptor(name = "DreamPlex", description = "plex client for enigma2", where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "pluginLogo.png", fnc=main))
	myList.append(PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = Autostart))
	myList.append(PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = sessionStart))
		
	if config.plugins.dreamplex.showInMainMenu.value:
		myList.append(PluginDescriptor(name="DreamPlex", description=_("plex client for enigma2"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_dreamplex))

	return myList