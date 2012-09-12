# -*- coding: UTF-8 -*-

# Copyright (C) 2010-2012 Ulteo SAS
# http://www.ulteo.com
# Author Laurent CLOUET <laurent@ulteo.com> 2010
# Author Julien LANGLOIS <julien@ulteo.com> 2010, 2011, 2012
# Author David LECHEVALIER <david@ulteo.com> 2012
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

import errno
import hashlib
import locale
import os
import pwd
import stat
import urllib
import urlparse

from ovd.Logger import Logger
from ovd.Role.ApplicationServer.Profile import Profile as AbstractProfile
from ovd.Platform.System import System

class Profile(AbstractProfile):
	MOUNT_POINT = "/mnt/ulteo/ovd"
	
	def init(self):
		self.profileMounted = False
		self.folderRedirection = []
		
		self.cifs_dst = os.path.join(self.MOUNT_POINT, self.session.id)
		self.profile_mount_point = os.path.join(self.cifs_dst, "profile")
		self.homeDir = None
	
	
	def mount_cifs(self, share, uri, dest):
		if share.has_key("login") and share.has_key("password"):
			cmd = "mount -t cifs -o username=%s,password=%s,uid=%s,gid=0,umask=077 //%s%s %s"%(share["login"], share["password"], self.session.user.name, uri.netloc, uri.path, dest)
		else:
			cmd = "mount -t cifs -o guest,uid=%s,gid=0,umask=077 //%s%s %s"%(self.session.user.name, uri.netloc, uri.path, dest)
		
		cmd = self.transformToLocaleEncoding(cmd)
		Logger.debug("Profile, share mount command: '%s'"%(cmd))
		p = System.execute(cmd)
		if p.returncode != 0:
			Logger.debug("CIFS mount failed (status: %d) => %s"%(p.returncode, p.stdout.read()))
			return False
		
		return True
	
	
	def mount_webdav(self, share, uri, dest):
		davfs_conf   = os.path.join(self.cifs_dst, "davfs.conf")
		davfs_secret = os.path.join(self.cifs_dst, "davfs.secret")
		if uri.scheme == "webdav":
			mount_uri = urlparse.urlunparse(("http", uri.netloc, uri.path, uri.params, uri.query, uri.fragment))
		else:
			mount_uri = urlparse.urlunparse(("https", uri.netloc, uri.path, uri.params, uri.query, uri.fragment))
		
		if not System.mount_point_exist(davfs_conf):
			f = open(davfs_conf, "w")
			f.write("ask_auth 0\n")
			f.write("use_locks 0\n")
			f.write("secrets %s\n"%(davfs_secret))
			f.close()
		
		if not System.mount_point_exist(davfs_secret):
			f = open(davfs_secret, "w")
			f.close()
			os.chmod(davfs_secret, stat.S_IRUSR | stat.S_IWUSR)
		
		if share.has_key("login") and share.has_key("password"):
			f = open(davfs_secret, "a")
			f.write("%s %s %s\n"%(mount_uri, share["login"], share["password"]))
			f.close()
		
		cmd = 'mount -t davfs -o conf=%s,uid=%s,gid=0,dir_mode=700,file_mode=600 "%s" %s'%(davfs_conf, self.session.user.name, mount_uri, dest)
		cmd = self.transformToLocaleEncoding(cmd)
		Logger.debug("Profile, sharedFolder mount command: '%s'"%(cmd))
		p = System.execute(cmd)
		if p.returncode != 0:
			Logger.debug("WebDAV mount failed (status: %d) => %s"%(p.returncode, p.stdout.read()))
			return False
		
		return True
	
	
	def mount(self):
		os.makedirs(self.cifs_dst)
		self.homeDir = pwd.getpwnam(self.transformToLocaleEncoding(self.session.user.name))[5]
		
		if self.profile is not None:
			os.makedirs(self.profile_mount_point)
			
			u = urlparse.urlparse(self.profile["uri"])
			if u.scheme == "cifs":
				ret = self.mount_cifs(self.profile, u, self.profile_mount_point)
			
			elif u.scheme in ("webdav", "webdavs"):
				ret = self.mount_webdav(self.profile, u, self.profile_mount_point)
			else:
				Logger.warn("Profile: unknown protocol in share uri '%s'"%(self.profile["uri"]))
				ret = False
			
			if ret is False:
				Logger.error("Profile mount failed")
				os.rmdir(self.profile_mount_point)
			else:
				self.profileMounted = True
		
		for sharedFolder in self.sharedFolders:
			dest = os.path.join(self.MOUNT_POINT, self.session.id, "sharedFolder_"+ hashlib.md5(sharedFolder["uri"]).hexdigest())
			if not System.mount_point_exist(dest):
				os.makedirs(dest)
			
			u = urlparse.urlparse(sharedFolder["uri"])
			if u.scheme == "cifs":
				ret = self.mount_cifs(sharedFolder, u, dest)
			
			elif u.scheme in ("webdav", "webdavs"):
				ret = self.mount_webdav(sharedFolder, u, dest)
			else:
				Logger.warn("Profile: unknown protocol in share uri '%s'"%(self.profile["uri"]))
				ret = False
			
			if ret is False:
				Logger.error("SharedFolder mount failed")
				os.rmdir(dest)
			else:
				sharedFolder["mountdest"] = dest
				home = self.homeDir
				
				dst = os.path.join(home, sharedFolder["name"])
				i = 0
				while System.mount_point_exist(dst):
					dst = os.path.join(home, sharedFolder["name"]+"_%d"%(i))
					i += 1
				
				if not System.mount_point_exist(dst):
					os.makedirs(dst)
				
				cmd = "mount -o bind \"%s\" \"%s\""%(dest, dst)
				cmd = self.transformToLocaleEncoding(cmd)
				Logger.debug("Profile bind dir command '%s'"%(cmd))
				p = System.execute(cmd)
				if p.returncode != 0:
					Logger.error("Profile bind dir failed")
					Logger.error("Profile bind dir failed (status: %d) %s"%(p.returncode, p.stdout.read()))
				else:
					sharedFolder["local_path"] = dst
					self.folderRedirection.append(dst)
					self.addGTKBookmark(dst)
		
		if self.profile is not None and self.profileMounted:
			for d in [self.DesktopDir, self.DocumentsDir]:
				src = os.path.join(self.profile_mount_point, d)
				dst = os.path.join(self.homeDir, d)
				
				while not System.mount_point_exist(src):
					try:
						os.makedirs(src)
					except OSError, err:
						if self.isNetworkError(err[0]):
							Logger.warn("Unable to access profile: %s"%(str(err)))
							return
						
						Logger.debug2("Profile mkdir failed (concurrent access because of more than one ApS) => %s"%(str(err)))
						continue
				
				if not System.mount_point_exist(dst):
					os.makedirs(dst)
				
				cmd = "mount -o bind \"%s\" \"%s\""%(src, dst)
				cmd = self.transformToLocaleEncoding(cmd)
				Logger.debug("Profile bind dir command '%s'"%(cmd))
				p = System.execute(cmd)
				if p.returncode != 0:
					Logger.error("Profile bind dir failed")
					Logger.error("Profile bind dir failed (status: %d) %s"%(p.returncode, p.stdout.read()))
				else:
					self.folderRedirection.append(dst)
			
			
			self.copySessionStart()
	
	
	def umount(self):
		if self.profile is not None and self.profileMounted:
			self.copySessionStop()
		
		while len(self.folderRedirection)>0:
			d = self.folderRedirection.pop()
			
			try:
				if not self.ismount(d):
					continue
			except IOError, err:
				Logger.error("Unable to check mount point %s :%s"%(d, str(err)))
			
			cmd = "umount \"%s\""%(d)
			cmd = self.transformToLocaleEncoding(cmd)
			Logger.debug("Profile bind dir command: '%s'"%(cmd))
			p = System.execute(cmd)
			if p.returncode != 0:
				Logger.error("Profile bind dir failed")
				Logger.error("Profile bind dir failed (status: %d) %s"%(p.returncode, p.stdout.read()))
		
		for sharedFolder in self.sharedFolders:
			if sharedFolder.has_key("mountdest"):
				cmd = """umount "%s" """%(sharedFolder["mountdest"])
				cmd = self.transformToLocaleEncoding(cmd)
				Logger.debug("Profile sharedFolder umount dir command: '%s'"%(cmd))
				p = System.execute(cmd)
				if p.returncode != 0:
					Logger.error("Profile sharedFolder umount dir failed")
					Logger.error("Profile sharedFolder umount dir failed (status: %d) %s"%(p.returncode, p.stdout.read()))
				
				os.rmdir(sharedFolder["mountdest"])
		
		for fname in ("davfs.conf", "davfs.secret"):
			path = os.path.join(self.cifs_dst, fname)
			if not System.mount_point_exist(path):
				continue
			try:
				os.remove(path)
			except OSError, e:
				Logger.error("Unable to delete file (%s): %s"%(path, str(e)))
		
		if self.profile is not None and self.profileMounted:
			cmd = "umount %s"%(self.profile_mount_point)
			cmd = self.transformToLocaleEncoding(cmd)
			Logger.debug("Profile umount command: '%s'"%(cmd))
			p = System.execute(cmd)
			if p.returncode != 0:
				Logger.error("Profile umount failed")
				Logger.debug("Profile umount failed (status: %d) => %s"%(p.returncode, p.stdout.read()))
			
			try:
				os.rmdir(self.profile_mount_point)
			except OSError, e:
				Logger.error("Unable to delete mount point (%s): %s"%(self.profile_mount_point, str(e)))
		
		try:		
			os.rmdir(self.cifs_dst)
		except OSError, e:
			Logger.error("Unable to delete profile (%s): %s"%(self.cifs_dst, str(e)))
	
	
	def copySessionStart(self):
		if self.homeDir is None or not os.path.isdir(self.homeDir):
			return
		
		d = os.path.join(self.profile_mount_point, "conf.Linux")
		if not System.mount_point_exist(d):
			return
		
		# Copy conf files
		cmd = self.getRsyncMethod(d, self.homeDir, True)
		Logger.debug("rsync cmd '%s'"%(cmd))
		
		p = System.execute(cmd)
		if p.returncode is not 0:
			Logger.error("Unable to copy conf from profile")
			Logger.debug("Unable to copy conf from profile, cmd '%s' return %d: %s"%(cmd, p.returncode, p.stdout.read()))
	
	
	def copySessionStop(self):
		if self.homeDir is None or not os.path.isdir(self.homeDir):
			return
		
		d = os.path.join(self.profile_mount_point, "conf.Linux")
		while not System.mount_point_exist(d):
			try:
				os.makedirs(d)
			except OSError, err:
				if self.isNetworkError(err[0]):
					Logger.warn("Unable to access profile: %s"%(str(err)))
					return
				
				Logger.debug2("conf.Linux mkdir failed (concurrent access because of more than one ApS) => %s"%(str(err)))
				continue
		
		# Copy conf files
		cmd = self.getRsyncMethod(self.homeDir, d)
		Logger.debug("rsync cmd '%s'"%(cmd))
		
		p = System.execute(cmd)
		if p.returncode is not 0:
			Logger.error("Unable to copy conf to profile")
			Logger.debug("Unable to copy conf to profile, cmd '%s' return %d: %s"%(cmd, p.returncode, p.stdout.read()))
	
	
	@staticmethod
	def getRsyncMethod(src, dst, owner=False):
		grep_cmd = " | ".join(['grep -v "/%s$"'%(word) for word in Profile.rsyncBlacklist()])
		find_cmd = 'find "%s" -maxdepth 1 -name ".*" | %s'%(src, grep_cmd)
		
		args = ["-rltD", "--safe-links"]
		if owner:
			args.append("-o")
		
		return 'rsync %s $(%s) "%s/"'%(" ".join(args), find_cmd, dst)
	
	
	@staticmethod
	def rsyncBlacklist():
		return [".gvfs", ".pulse", ".pulse-cookie", ".rdp_drive", ".Trash", ".vnc"]
	
	
	@staticmethod
	def transformToLocaleEncoding(data):
		try:
			encoding = locale.getpreferredencoding()
		except:
			encoding = "UTF-8"
		
		return data.encode(encoding)
	
	
	@staticmethod
	def ismount(path):
		# The content returned by /proc/mounts escape space using \040
		escaped_path = path.replace(" ", "\\040")
		
		for line in file('/proc/mounts'):
			components = line.split()
			if len(components) > 1 and components[1] == escaped_path:
				return True
		
		return False
	
	
	@staticmethod
	def isNetworkError(err):
		networkError = [errno.EIO, errno.ECOMM,
				errno.ENETDOWN,
				errno.ENETUNREACH,
				errno.ENETRESET,
				errno.ECONNABORTED,
				errno.ECONNRESET,
				errno.ENOTCONN,
				errno.ESHUTDOWN,
				errno.ECONNREFUSED,
				errno.EHOSTDOWN,
				errno.EHOSTUNREACH
				]
		return err in networkError
	
	
	def addGTKBookmark(self, url):
		url = self.transformToLocaleEncoding(url)
		url = urllib.pathname2url(url)
		
		path = os.path.join(self.homeDir, ".gtk-bookmarks")
		f = file(path, "a")
		f.write("file://%s\n"%(url))
		f.close()
	
	
	def register_shares(self, dest_dir):
		if self.profileMounted is True:
			path = os.path.join(dest_dir, self.profile["rid"])
			f = file(path, "w")
			f.write(self.homeDir)
			f.close()
		
		for sharedFolder in self.sharedFolders:
			if not sharedFolder.has_key("local_path"):
				continue
			
			path = os.path.join(dest_dir, sharedFolder["rid"])
			f = file(path, "w")
			f.write(self.transformToLocaleEncoding(sharedFolder["local_path"]))
			f.close()
