# -*- coding: utf-8 -*-
#===============================================================================
# IMPORT
#===============================================================================
from Plugins.Plugin import PluginDescriptor

from Components.Network import iNetwork
from Components.config import config, configfile

from DP_Player import DP_Player

from __init__ import prepareEnvironment, startEnvironment, _ # _ is translation
from __common__ import getUUID, saveLiveTv, getLiveTv

#===============================================================================
# GLOBALS
#===============================================================================
HttpDeamonThread = None
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

		if config.plugins.dreamplex.remoteAgent.value:
			startRemoteDeamon()
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
	HttpDeamonThread.PlayerDataPump.recv_msg.get().append(gotThreadMsg)
	runningWithoutErrors = HttpDeamonThread.startDeamon()

	if not runningWithoutErrors:
		HttpDeamonStarted = False
	else:
		# we need this to avoid gs if users sets remoteplayer on and restarts. in this case there is false and we do not try to stop
		HttpDeamonStarted = True

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

#===========================================================================
#
#===========================================================================
def networkStart(reason, **kwargs):
	if reason is True and config.plugins.dreamplex.remoteAgent.value and HttpDeamonStarted:
		try:
			for adaptername in iNetwork.ifaces:
				if iNetwork.ifaces[adaptername]['up'] is True:
					HttpDeamonThread.setSession(global_session)
		except Exception:
			pass

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
	myList.append(PluginDescriptor(where = PluginDescriptor.WHERE_NETWORKCONFIG_READ, fnc = networkStart))

	if config.plugins.dreamplex.showInMainMenu.value:
		myList.append(PluginDescriptor(name="DreamPlex", description=_("plex client for enigma2"), where = [PluginDescriptor.WHERE_MENU], fnc=menu_dreamplex))

	return myList
