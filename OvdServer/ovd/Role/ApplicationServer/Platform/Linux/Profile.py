# -*- coding: UTF-8 -*-

# Copyright (C) 2010 Ulteo SAS
# http://www.ulteo.com
# Author Julien LANGLOIS <julien@ulteo.com> 2010
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

import commands
import hashlib
import os
import pwd

from ovd.Logger import Logger
from ovd.Role.ApplicationServer.Profile import Profile as AbstractProfile

class Profile(AbstractProfile):
	MOUNT_POINT = "/mnt/ulteo/ovd"
	
	def init(self):
		self.profileMounted = False
		self.folderRedirection = []
		
		self.cifs_dst = os.path.join(self.MOUNT_POINT, self.session.id)
		self.profile_mount_point = os.path.join(self.cifs_dst, "profile")
		self.homeDir = None
	
	
	def mount(self):
		os.makedirs(self.profile_mount_point)
		
		if self.profile is not None:
			cmd = "mount -t cifs -o username=%s,password=%s,uid=%s,gid=0,umask=077 //%s/%s %s"%(self.profile["login"], self.profile["password"], self.session.user.name, self.profile["server"], self.profile["dir"], self.profile_mount_point)
			Logger.debug("Profile mount command: '%s'"%(cmd))
			s,o = commands.getstatusoutput(cmd)
			if s != 0:
				Logger.error("Profile mount failed")
				Logger.debug("Profile mount failed (status: %d) => %s"%(s, o))
			else:
				self.profileMounted = True
		
		for sharedFolder in self.sharedFolders:
			dest = os.path.join(self.MOUNT_POINT, self.session.id, "sharedFolder_"+ hashlib.md5(sharedFolder["server"]+ sharedFolder["dir"]).hexdigest())
			if not os.path.exists(dest):
				os.makedirs(dest)
			
			print "mount dest ",dest
			cmd = "mount -t cifs -o username=%s,password=%s,uid=%s,gid=0,umask=077 //%s/%s %s"%(sharedFolder["login"], sharedFolder["password"], self.session.user.name, sharedFolder["server"], sharedFolder["dir"], dest)
			Logger.debug("Profile, sharedFolder mount command: '%s'"%(cmd))
			s,o = commands.getstatusoutput(cmd)
			if s != 0:
				Logger.error("Profile sharedFolder mount failed")
				Logger.debug("Profile sharedFolder mount failed (status: %d) => %s"%(s, o))
			else:
				sharedFolder["mountdest"] = dest
				home = pwd.getpwnam(self.session.user.name)[5]
				dst = os.path.join(home, sharedFolder["name"])
				i = 0
				while os.path.exists(dst):
					dst = os.path.join(home, sharedFolder["name"]+"_%d"%(i))
					i += 1
				
				if not os.path.exists(dst):
					os.makedirs(dst)
				
				cmd = "mount -o bind \"%s\" \"%s\""%(dest, dst)
				Logger.debug("Profile bind dir command '%s'"%(cmd))
				s,o = commands.getstatusoutput(cmd)
				if s != 0:
					Logger.error("Profile bind dir failed")
					Logger.error("Profile bind dir failed (status: %d) %s"%(s, o))
				else:
					self.folderRedirection.append(dst)
		
		if self.profile is not None:
			self.homeDir = pwd.getpwnam(self.session.user.name)[5]
			for d in [self.DesktopDir, self.DocumentsDir]:
				src = os.path.join(self.profile_mount_point, d)
				dst = os.path.join(self.homeDir, d)
				
				if not os.path.exists(src):
					os.makedirs(src)
				
				if not os.path.exists(dst):
					os.makedirs(dst)
				
				cmd = "mount -o bind \"%s\" \"%s\""%(src, dst)
				Logger.debug("Profile bind dir command '%s'"%(cmd))
				s,o = commands.getstatusoutput(cmd)
				if s != 0:
					Logger.error("Profile bind dir failed")
					Logger.error("Profile bind dir failed (status: %d) %s"%(s, o))
				else:
					self.folderRedirection.append(dst)
			
			
			self.copySessionStart()
	
	
	def umount(self):
		if self.profile is not None:
			self.copySessionStop()
		
		while len(self.folderRedirection)>0:
			d = self.folderRedirection.pop()
			
			if not os.path.ismount(d):
				continue
			
			cmd = "umount \"%s\""%(d)
			Logger.debug("Profile bind dir command: '%s'"%(cmd))
			s,o = commands.getstatusoutput(cmd)
			if s != 0:
				Logger.error("Profile bind dir failed")
				Logger.error("Profile bind dir failed (status: %d) %s"%(s, o))
		
		for sharedFolder in self.sharedFolders:
			if sharedFolder.has_key("mountdest"):
				cmd = """umount "%s" """%(sharedFolder["mountdest"])
				Logger.debug("Profile sharedFolder umount dir command: '%s'"%(cmd))
				s,o = commands.getstatusoutput(cmd)
				if s != 0:
					Logger.error("Profile sharedFolder umount dir failed")
					Logger.error("Profile sharedFolder umount dir failed (status: %d) %s"%(s, o))
				
				os.rmdir(sharedFolder["mountdest"])
		
		if self.profile is not None and self.profileMounted:
			cmd = "umount %s"%(self.profile_mount_point)
			Logger.debug("Profile umount command: '%s'"%(cmd))
			s,o = commands.getstatusoutput(cmd)
			if s != 0:
				Logger.error("Profile umount failed")
				Logger.debug("Profile umount failed (status: %d) => %s"%(s, o))
			
			os.rmdir(self.profile_mount_point)
		
		os.rmdir(self.cifs_dst)
	
	def copySessionStart(self):
		if self.homeDir is None or not os.path.isdir(self.homeDir):
			return
		
		d = os.path.join(self.profile_mount_point, "conf.Linux")
		if not os.path.exists(d):
			return
		
		# Copy conf files
		cmd = self.getRsyncMethod(d, self.homeDir, True)
		Logger.debug("rsync cmd '%s'"%(cmd))
		
		s,o = commands.getstatusoutput(cmd)
		if s is not 0:
			Logger.error("Unable to copy conf from profile")
			Logger.debug("Unable to copy conf from profile, cmd '%s' return %d: %s"%(cmd, s, o))
	
	
	def copySessionStop(self):
		if self.homeDir is None or not os.path.isdir(self.homeDir):
			return
		
		d = os.path.join(self.profile_mount_point, "conf.Linux")
		if not os.path.exists(d):
			os.makedirs(d)
		
		# Copy conf files
		cmd = self.getRsyncMethod(self.homeDir, d)
		Logger.debug("rsync cmd '%s'"%(cmd))
		
		s,o = commands.getstatusoutput(cmd)
		if s is not 0:
			Logger.error("Unable to copy conf to profile")
			Logger.debug("Unable to copy conf to profile, cmd '%s' return %d: %s"%(cmd, s, o))
	
	@staticmethod
	def getRsyncMethod(src, dst, owner=False):
		grep_cmd = " | ".join(['grep -v "/%s$"'%(word) for word in Profile.rsyncBlacklist()])
		find_cmd = 'find "%s" -maxdepth 1 -name ".*" | %s'%(src, grep_cmd)
		
		args = ["-rltD", "--max-size=20"]
		if owner:
			args.append("-o")
		
		return 'rsync %s $(%s) "%s/"'%(" ".join(args), find_cmd, dst)
	
	@staticmethod
	def rsyncBlacklist():
		return [".gvfs", ".pulse", ".pulse-cookie", ".rdp_drive", ".Trash", ".vnc"]
