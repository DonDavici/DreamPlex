# -*- coding: utf-8 -*-
#===============================================================================
# IMPORT
#===============================================================================
from Plugins.Plugin import PluginDescriptor

try:
	from Components.Network import iNetworkInfo
except:
	from Components.Network import iNetwork

from Components.config import config, configfile

from DP_Player import DP_Player

from __init__ import prepareEnvironment, startEnvironment, _ # _ is translation
from __common__ import getUUID, saveLiveTv, getLiveTv, getOeVersion

#===============================================================================
# GLOBALS
#===============================================================================
HttpDeamonThread = None
HttpDeamonThreadConn = None
HttpDeamonStarted = False
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

	# save liveTvData
	saveLiveTv(global_session.nav.getCurrentlyPlayingServiceReference())

	# this loads the skin
	startEnvironment()

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
		getUUID()

	else:
		config.plugins.dreamplex.entriescount.save()
		config.plugins.dreamplex.Entries.save()
		config.plugins.dreamplex.save()
		configfile.save()

		if config.plugins.dreamplex.remoteAgent.value and HttpDeamonStarted:
			HttpDeamonThread.stopRemoteDeamon()

#===========================================================================
#
#===========================================================================
def startRemoteDeamon():
	from DPH_RemoteListener import HttpDeamon
	global HttpDeamonThread
	global HttpDeamonStarted

	# we use the global g_mediaSyncerInfo.instance to take care only having one instance
	HttpDeamonThread = HttpDeamon()

	if getOeVersion() != "oe22":
		HttpDeamonThread.PlayerDataPump.recv_msg.get().append(gotThreadMsg)
	else:
		global HttpDeamonThreadConn
		HttpDeamonThreadConn = HttpDeamonThread.PlayerDataPump.recv_msg.connect(gotThreadMsg)

	HttpDeamonThread.prepareDeamon() # we just prepare. we are starting only on networkStart with HttpDeamonThread.setSession
	HttpDeamonStarted = HttpDeamonThread.getDeamonState()[1]

	if HttpDeamonStarted:
		HttpDeamonThread.setSession(global_session)
	else:
		HttpDeamonThread.stopRemoteDeamon()

#===========================================================================
#
#===========================================================================
def getHttpDeamonInformation():
	return HttpDeamonThread.getDeamonState()

#===========================================================================
# msg as second params is needed -. do not remove even if it is not used
# form outside!!!!
#===========================================================================
# noinspection PyUnusedLocal
def gotThreadMsg(msg):
	msg = HttpDeamonThread.PlayerData.pop()

	data = msg[0]

	listViewList    = data["listViewList"]
	currentIndex    = data["currentIndex"]
	libraryName     = data["libraryName"]
	autoPlayMode    = data["autoPlayMode"]
	resumeMode      = data["resumeMode"]
	playbackMode    = data["playbackMode"]
	forceResume     = data["forceResume"]

	# load skin data here as well
	startEnvironment()

	# save liveTvData
	saveLiveTv(global_session.nav.getCurrentlyPlayingServiceReference())

	# now we start the player
	global_session.openWithCallback(restoreLiveTv, DP_Player, listViewList, currentIndex, libraryName, autoPlayMode, resumeMode, playbackMode, forceResume=forceResume)

#===========================================================================
#
#===========================================================================
def restoreLiveTv(retval):
	global_session.nav.playService(getLiveTv())

#===========================================================================
#
#===========================================================================
def sessionStart(reason, **kwargs):

	if "session" in kwargs:
		global global_session
		global_session = kwargs["session"]

		if config.plugins.dreamplex.remoteAgent.value:
			startRemoteDeamon()

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
