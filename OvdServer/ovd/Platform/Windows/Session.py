# -*- coding: UTF-8 -*-

# Copyright (C) 2009 Ulteo SAS
# http://www.ulteo.com
# Author Julien LANGLOIS <julien@ulteo.com> 2009
#
# This program is free software; you can redistribute it and/or 
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import random
import time
import win32api
from win32com.shell import shell, shellcon
import win32con
import win32file
import win32net
import win32profile
import win32security
import _winreg

from ovd.Logger import Logger
from ovd.Role.ApplicationServer.Session import Session as AbstractSession

from Platform import Platform
import Reg

class Session(AbstractSession):
	def __init__(self, infos):
		AbstractSession.__init__(self, infos)
		self.user_password = infos["password"]
	
	
	def install_client(self):
		(logon, profileDir) = self.init()
		
		programsDir = shell.SHGetSpecialFolderPath(logon, shellcon.CSIDL_PROGRAMS)
		print "startmenu: ",programsDir
		
				
		#desktopDir = shell.SHGetSpecialFolderPath(logon, shellcon.CSIDL_DESKTOPDIRECTORY)
		# bug: this return the Administrator desktop dir path ...
		desktopDir = os.path.join(profileDir, "Desktop")
		print "desktop dir",desktopDir
		
		
		# remove default startmenu
		if os.path.exists(programsDir):
			Platform.DeleteDirectory(programsDir)
		os.makedirs(programsDir)
		
		for (app_id, app_target) in self.applications:
			final_file = os.path.join(programsDir, os.path.basename(app_target))
			
			# todo: make a new shortcut from the old one to use the same as startovdapp
			win32file.CopyFile(app_target, final_file, True)
		
		if self.parameters.has_key("desktop_icons"):
			if not os.path.exists(desktopDir):
				os.makedirs(desktopDir)
			
			for (app_id, app_target) in self.applications:
				final_file = os.path.join(desktopDir, os.path.basename(app_target))
			
				# todo: make a new shortcut from the old one to use the same as startovdapp
				if os.path.exists(final_file):
					os.remove(final_file)
				win32file.CopyFile(app_target, final_file, True)


	
	def uninstall_client(self):
		sid = self.getSid()
		if sid is None:
			return False

		if not self.deleteProfile(sid):
			if not self.unload(sid):
				Logger.error("Unable to unload User reg key")
				return False
			
			if not self.deleteProfile(sid):
				Logger.error("Unable to delete profile")
				return False
		
		
		# ToDo: remove the HKLM regitry key
		
		return True
	
	
	def deleteProfile(self, sid):
		try:
			win32profile.DeleteProfile(sid)
		except:
			return False
	
		return True
	
	
	def init(self):
		"""Init profile repo"""
		
		# Set some TS settings
		#win32ts.WTSSetUserConfig(None, self.login , win32ts.WTSUserConfigInitialProgram, r"OVDShell.exe")
		#win32ts.WTSSetUserConfig(None, self.login , win32ts.WTSUserConfigfInheritInitialProgram, False)
	
		logon = win32security.LogonUser(self.user_login, None, self.user_password, win32security.LOGON32_LOGON_INTERACTIVE, win32security.LOGON32_PROVIDER_DEFAULT)
		
		data = {}
		data["UserName"] = self.user_login
		
		hkey = win32profile.LoadUserProfile(logon, data)
		#self.init_ulteo_registry(sid)
		#self.init_redirection_shellfolders(sid)
		win32profile.UnloadUserProfile(logon, hkey)
		
		profileDir = win32profile.GetUserProfileDirectory(logon)
		
		print "profiledir:",profileDir
		self.overwriteDefaultRegistry(profileDir)
		
		return (logon, profileDir)
		
	
	
	def unload(self, sid):
		try:
			# Unload user reg
			win32api.RegUnLoadKey(win32con.HKEY_USERS, sid)
			win32api.RegUnLoadKey(win32con.HKEY_USERS, sid+'_Classes')
		except Exception, e:
			print "Unable to unload user reg: ",str(e)
			return False
		
		return True
	
	def getSid(self):
		#get the sid
		try:
			sid, _, _ = win32security.LookupAccountName(None, self.user_login)
			sid = win32security.ConvertSidToStringSid(sid)
		except Exception,e:
			Logger.warn("Unable to get SID: %s"%(str(e)))
			return None
		
		return sid
	
	
	def overwriteDefaultRegistry(self, directory):
		registryFile = os.path.join(directory, "NTUSER.DAT")
		
		# Get some privileges to load the hive
		priv_flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
		hToken = win32security.OpenProcessToken (win32api.GetCurrentProcess (), priv_flags)
		backup_privilege_id = win32security.LookupPrivilegeValue (None, "SeBackupPrivilege")
		restore_privilege_id = win32security.LookupPrivilegeValue (None, "SeRestorePrivilege")
		win32security.AdjustTokenPrivileges (
			hToken, 0, [
			(backup_privilege_id, win32security.SE_PRIVILEGE_ENABLED),
			(restore_privilege_id, win32security.SE_PRIVILEGE_ENABLED)
			]
		)


		hiveName = "OVD_%d"%(random.randrange(10000, 50000))
		
		# Load the hive
		_winreg.LoadKey(win32con.HKEY_USERS, hiveName, registryFile)
		
		# Policies update
		path = r"%s\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"%(hiveName)
		restrictions = ["DisableFavoritesDirChange",
				"DisableLocalMachineRun",
				"DisableLocalMachineRunOnce",
				"DisableMachineRunOnce",
				"DisableMyMusicDirChange",
				"DisableMyPicturesDirChange",
				"DisablePersonalDirChange",
				"EnforceShellExtensionSecurity",
				#"ForceStartMenuLogOff",
				"Intellimenus",
				"NoChangeStartMenu",
				"NoClose",
				"NoCommonGroups",
				"NoControlPanel",
				"NoDFSTab",
				"NoFind",
				"NoFolderOptions",
				"NoHardwareTab",
				"NoInstrumentation",
				"NoIntellimenus",
				"NoInternetIcon", # remove the IE icon
				"NoManageMyComputerVerb",
				"NonEnum",
				"NoNetworkConnections",
				"NoResolveSearch",
				"NoRun",
				"NoSetFolders",
				"NoSetTaskbar",
				"NoStartMenuSubFolders", # should remove the folders from startmenu but doesn't work
				"NoSMBalloonTip",
				"NoStartMenuEjectPC",
				"NoStartMenuNetworkPlaces",
				"NoTrayContextMenu",
				"NoWindowsUpdate",
				#"NoViewContextMenu", # Mouse right clic
				#"StartMenuLogOff",
				]
		
		key = _winreg.OpenKey(_winreg.HKEY_USERS, path, 0, _winreg.KEY_SET_VALUE)
		for item in restrictions:
			_winreg.SetValueEx(key, item, 0, _winreg.REG_DWORD, 1)
		_winreg.CloseKey(key)
		
		
		path = r"%s\Software\Microsoft\Windows\CurrentVersion\Policies"%(hiveName)
		key = _winreg.OpenKey( _winreg.HKEY_USERS, path, 0, _winreg.KEY_SET_VALUE)
		_winreg.CreateKey(key, "System")
		_winreg.CloseKey(key)
		
		path = r"%s\Software\Microsoft\Windows\CurrentVersion\Policies\System"%(hiveName)
		restrictions = ["DisableRegistryTools",
				"DisableTaskMgr",
				"NoDispCPL",
				]
		
		key = _winreg.OpenKey(_winreg.HKEY_USERS, path, 0, _winreg.KEY_SET_VALUE)
		for item in restrictions:
			_winreg.SetValueEx(key, item, 0, _winreg.REG_DWORD, 1)
		_winreg.CloseKey(key)
		
		
		
		
		# Desktop customization
		path = r"%s\Control Panel\Desktop"%(hiveName)
		items = ["ScreenSaveActive", "ScreenSaverIsSecure"]
		
		key = _winreg.OpenKey(_winreg.HKEY_USERS, path, 0, _winreg.KEY_SET_VALUE)
		for item in items:
			_winreg.SetValueEx(key, item, 0, _winreg.REG_DWORD, 1)
		_winreg.CloseKey(key)
		
		
		# Rediect the Shell Folders to the remote profile
		path = r"%s\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"%(hiveName)
		data = [
			"Desktop",
		]
		key = win32api.RegOpenKey(win32con.HKEY_USERS, path, 0, win32con.KEY_SET_VALUE)
		
		for item in data:
			dst = os.path.join(directory, item)
			win32api.RegSetValueEx(key, item, 0, win32con.REG_SZ, dst)
		win32api.RegCloseKey(key)
		
		
		# Overwrite Active Setup : doesn't work !
		#path = r"Software\Microsoft\Active Setup"
		#hkey_src = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, path, 0, win32con.KEY_ALL_ACCESS)
		
		#path = r"%s\%s"%(hiveName, path)
		#hkey_dst = win32api.RegOpenKey(win32con.HKEY_USERS, path, 0, win32con.KEY_ALL_ACCESS)
		
		#try:
			#CopyTree(hkey_src, "Installed Components", hkey_dst)
		#except Exception, err:
			#import traceback
			#import sys
			#exception_type, exception_string, tb = sys.exc_info()
			#trace_exc = "".join(traceback.format_tb(tb))
			#print trace_exc
			#print exception_string
		
		#win32api.RegCloseKey(hkey_src)
		#win32api.RegCloseKey(hkey_dst)
		
		
		# Unload the hive
		win32api.RegUnLoadKey(win32con.HKEY_USERS, hiveName)
	
	
	
	def init_ulteo_registry(self, sid):
		#		# Set settings to OVDShell be able to mount remote profile
		path = sid+r"\Software"
		subkey = r"Ulteo Session"
		key = win32api.RegOpenKey(win32con.HKEY_USERS, path, 0, win32con.KEY_SET_VALUE)
		win32api.RegCreateKey(key, subkey)
		win32api.RegCloseKey(key)
		
		profile = r"\\10.42.1.254\julien\profile"
		
		path+= r"\%s"%(subkey)
		data = {}
		data["shell"] = "explorer" # seamlessrdpshell
		data["profile"] = r"%s\common"%(profile)
		data["profile_local"] = r"Z:"
		data["profile_username"] = "julien"
		data["profile_password"] = "test"
	
		key = win32api.RegOpenKey(win32con.HKEY_USERS, path, 0, win32con.KEY_SET_VALUE)
		
		for (k,v) in data.items():
			win32api.RegSetValueEx(key, k, 0, win32con.REG_SZ, v)
		
		win32api.RegCloseKey(key)
		
	def init_redirection_shellfolders(self, sid):
		# Rediect the Shell Folders to the remote profile
		path = sid+r"\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
		data = [
			"Desktop",
			"AppData",
			"Start Menu",
			"Personal",
			"Recent",
		]
		key = win32api.RegOpenKey(win32con.HKEY_USERS, path, 0, win32con.KEY_SET_VALUE)
		
		for item in data:
			win32api.RegSetValueEx(key, item, 0, win32con.REG_SZ, r"Z:\%s"%(item))
		
		win32api.RegCloseKey(key)
	
		
		
