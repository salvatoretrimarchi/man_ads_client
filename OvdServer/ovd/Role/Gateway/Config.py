# -*- coding: utf-8 -*-

# Copyright (C) 2011-2013 Ulteo SAS
# http://www.ulteo.com
# Author Julien LANGLOIS <julien@ulteo.com> 2011
# Author Samuel BOVEE <samuel@ulteo.com> 2011
# Author David LECHEVALIER <david@ulteo.com> 2012
# Author Alexandre CONFIANT-LATOUR <a.confiant@ulteo.com> 2013
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

import socket
import re
from urlparse import urlparse

from ovd.Logger import Logger


class Protocol:
	HTTP = 80
	HTTPS = 443
	RDP = 3389



class Config:
	general = None
	address = "0.0.0.0"
	port = 443
	max_process = 10
	max_connection = 100
	process_timeout = 60
	connection_timeout = 10
	http_max_header_size = 2048
	web_client = None
	admin_redirection = False
	root_redirection = None
	http_keep_alive = True
	disable_sslv2 = False
	force_buffering = ["/ovd/client/start", "/ovd/client/start.php"]

	@classmethod
	def init(cls, infos):
		if infos.has_key("address"):
			cls.address = infos["address"]
		
		if infos.has_key("port") and infos["port"].isdigit():
			try:
				cls.port = int(infos["port"])
			except ValueError:
				Logger.error("Invalid int number for port")
		
		if infos.has_key("connection_timeout") and infos["connection_timeout"].isdigit():
			try:
				cls.connection_timeout = int(infos["connection_timeout"])
			except ValueError:
				Logger.error("Invalid int number for connection_timeout")

		if infos.has_key("http_max_header_size") and infos["http_max_header_size"].isdigit():
			try:
				cls.http_max_header_size = int(infos["http_max_header_size"])
			except ValueError:
				Logger.error("Invalid int number for http_max_header_size")
		
		if infos.has_key("max_process"):
			try:
				cls.max_process = int(infos["max_process"])
			except ValueError:
				Logger.error("Invalid int number for max_process")
		
		if infos.has_key("max_connection"):
			try:
				cls.max_connection = int(infos["max_connection"])
			except ValueError:
				Logger.error("Invalid int number for max_process")
		
		if infos.has_key("process_timeout"):
			try:
				cls.process_timeout = int(infos["process_timeout"])
			except ValueError:
				Logger.error("Invalid int number for process_timeout")
		
		if infos.has_key("web_client"):
			wc = infos["web_client"]
			if wc[:wc.find("://")] not in ["http", "https"]:
				wc = "http://" + infos["web_client"]
			url = urlparse(wc)
			try:
				if not url.hostname or url.params or url.query or url.fragment:
					raise Exception("url malformed")
				ip = socket.gethostbyname(url.hostname)
				if url.port and url.port <= 0 and url.port > 65536:
					raise Exception("incorrect port")
			except socket.gaierror:
				Logger.error("Invalid conf for Web Client: incorrect IP")
			except Exception, e:
				Logger.error("Invalid conf for Web Client: " + str(e))
			else:
				protocol = getattr(Protocol, url.scheme.upper())
				if url.port:
					port = url.port
				else:
					port = protocol
				cls.web_client = (protocol, ip, port)
		
		if infos.has_key("admin_redirection"):
			if infos["admin_redirection"].lower() == "true":
				cls.admin_redirection = True
			elif infos["admin_redirection"].lower() == "false":
				cls.admin_redirection = False
			else:
				Logger.error("Invalid value for 'admin_redirection' option")
		
		if infos.has_key("root_redirection") and infos["root_redirection"]:
			cls.root_redirection = infos["root_redirection"].lstrip('/')
		
		if infos.has_key("http_keep_alive"):
			if infos["http_keep_alive"].lower() == "false":
				cls.http_keep_alive = False
			elif infos["http_keep_alive"].lower() == "true":
				cls.http_keep_alive = True
			else:
				Logger.error("Invalid value for 'http_keep_alive' option")
		
		if infos.has_key("disable_sslv2"):
			if infos["disable_sslv2"].lower() == "false":
				cls.disable_sslv2 = False
			elif infos["disable_sslv2"].lower() == "true":
				cls.disable_sslv2 = True
			else:
				Logger.error("Invalid value for 'disable_sslv2' option")

		if infos.has_key("force_buffering"):
			cls.force_buffering = re.findall("(\S+)", infos["force_buffering"])

		
		return True
