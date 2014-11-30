# -*- coding: utf-8 -*-
#===============================================================================
# IMPORT
#===============================================================================
from Plugins.Plugin import PluginDescriptor
from Screens.Standby import inStandby

try:
	from Components.Network import iNetworkInfo
except:
	from Components.Network import iNetwork

from Components.config import config, configfile

from DP_Player import DP_Player
from enigma import eTimer

from __init__ import prepareEnvironment, startEnvironment, _ # _ is translation
from __common__ import getUUID, saveLiveTv, getLiveTv, getOeVersion

#===============================================================================
# GLOBALS
#===============================================================================
HttpDeamonThread = None
HttpDeamonThreadConn = None
HttpDeamonStarted = False
global_session = None
playbackIsRunning = False
notifyWatcher = None
notifyWatcherConn = None

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
	global playbackIsRunning

	data = msg[0]

	# first we check if we are standby and exit this if needed
	if inStandby is not None:
		inStandby.Power()

	if not playbackIsRunning:
		if "command" in data:
			if data["command"] == "startNotifier":
				startNotifier()

		else:
			listViewList    = data["listViewList"]
			currentIndex    = data["currentIndex"]
			libraryName     = data["libraryName"]
			autoPlayMode    = data["autoPlayMode"]
			resumeMode      = data["resumeMode"]
			playbackMode    = data["playbackMode"]
			forceResume     = data["forceResume"]
			subtitleData    = data["subtitleData"]

			# load skin data here as well
			startEnvironment()

			# save liveTvData
			saveLiveTv(global_session.nav.getCurrentlyPlayingServiceReference())

			playbackIsRunning = True

			# now we start the player
			global_session.open(DP_Player, listViewList, currentIndex, libraryName, autoPlayMode, resumeMode, playbackMode, forceResume=forceResume, subtitleData=subtitleData, startedByRemotePlayer=True)

	else:
		if "command" in data:
			command = data["command"]

			if command == "pause":
				global_session.current_dialog.pauseService()

			elif command == "play":
				global_session.current_dialog.unPauseService()

			elif command == "skipNext":
				pass

			elif command == "skipPrevious":
				pass

			elif command == "stepForward":
				pass

			elif command == "stepBack":
				pass

			elif command == "setVolume":
				global_session.current_dialog.setVolume(data["volume"])

			elif command == "stop":
				global_session.current_dialog.leavePlayerConfirmed(True)
				global_session.nav.playService(getLiveTv())

				playbackIsRunning = False

			elif command == "startNotifier":
				startNotifier()

			elif command == "stopNotifier":
				pass

			else:
				# not handled command
				print command
				raise Exception

#===========================================================================
#
#===========================================================================
def startNotifier():
	global notifyWatcher
	global notifyWatcherConn
	notifyWatcher = eTimer()

	if getOeVersion() != "oe22":
		notifyWatcher.callback.append(notifySubscribers)
	else:
		notifyWatcherConn = notifyWatcher.timeout.connect(notifySubscribers)

	notifyWatcher.start(1,False)

#===========================================================================
#
#===========================================================================
def notifySubscribers():
	if getPlayer is not None:
		HttpDeamonThread.notifySubscribers(getPlayer)

#===========================================================================
#
#===========================================================================
def getPlayer():
	ret = None

	try:
		ret = {}
		ret = global_session.current_dialog.getPlayer()
	except:
		pass

	return ret

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
