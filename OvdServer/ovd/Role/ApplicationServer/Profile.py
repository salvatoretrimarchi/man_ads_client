# -*- coding: UTF-8 -*-

# Copyright (C) 2010-2013 Ulteo SAS
# http://www.ulteo.com
# Author Julien LANGLOIS <julien@ulteo.com> 2010
# Author David LECHEVALIER <david@ulteo.com> 2013
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


class Profile:
	DesktopDir = "Desktop"
	DocumentsDir = "Documents"
	
	def __init__(self, session):
		self.session = session
		
		self.profile = None
		self.sharedFolders = []
		
		self.session.profile = self
		self.init()
	
	@staticmethod
	def cleanup():
		raise NotImplementedError()
	
	def init(self):
		raise NotImplementedError()
	
	def setProfile(self, profile):
		self.profile = profile
	
	def addSharedFolder(self, folder):
		self.sharedFolders.append(folder)
	
	def mount(self):
		raise NotImplementedError()
	
	def umount(self):
		raise NotImplementedError()
