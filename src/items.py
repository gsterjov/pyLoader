#
#    Copyright 2012 Goran Sterjov
#    This file is part of pyLoader.
#
#    pyLoader is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyLoader is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pyLoader.  If not, see <http://www.gnu.org/licenses/>.
#

from gi.repository import GObject

from pyload.ttypes import DownloadStatus


class Item (GObject.Object):
	'''
	A queue item that can either be a package or a link
	'''
	def __init__ (self, is_package=False, is_link=False):
		'''
		Constructor
		'''
		GObject.Object.__init__ (self)
		
		self.is_package = is_package
		self.is_link = is_link



class Package (Item):
	'''
	A package contains links to be downloaded within the same folder
	'''
	def __init__ (self, client, data):
		'''
		Constructor
		'''
		Item.__init__ (self, is_package=True)
		
		self.client = client
		
		self.id = data.pid
		self.name = data.name
		self.folder = data.folder
		self.site = data.site
		self.password = data.password
		self.dest = data.dest
		self.order = data.order
		
		self.links_done = data.linksdone
		self.links_total = data.linkstotal
		self.size_done = data.sizedone
		self.size_total = data.sizetotal

		self.links = []
		self.update_links()
	
	
	def update_links (self):
		self.links = []
		
		data = self.client.getPackageData (self.id)
		
		for link in data.links:
			self.links.append (Link (link))


	@property
	def finished (self):
		return self.links_done == self.links_total


	@property
	def links_online (self):
		online = 0
		for link in self.links:
			if link.status == Link.Status.ONLINE:
				online += 1

		return online


	@property
	def links_offline (self):
		offline = 0
		for link in self.links:
			if link.status in [Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				offline += 1
				
		return offline
	
	
	def __repr__ (self):
		return "<Package id: {0}, name: {1}>".format (self.id, self.name)



class Link (Item):
	'''
	A link to a file to be downloaded
	'''

	class Status (object):
		'''
		The various states that a link can find itself in
		'''
		STARTING		= DownloadStatus.Starting
		DECRYPTING		= DownloadStatus.Decrypting
		PROCESSING		= DownloadStatus.Processing
		ONLINE			= DownloadStatus.Online
		OFFLINE			= DownloadStatus.Offline
		QUEUED			= DownloadStatus.Queued
		SKIPPED			= DownloadStatus.Skipped
		WAITING			= DownloadStatus.Waiting
		DOWNLOADING		= DownloadStatus.Downloading
		FAILED			= DownloadStatus.Failed
		ABORTED			= DownloadStatus.Aborted
		FINISHED		= DownloadStatus.Finished
		TEMP_OFFLINE	= DownloadStatus.TempOffline
		CUSTOM			= DownloadStatus.Custom
		UNKNOWN			= DownloadStatus.Unknown
		
		_STATUS_STR = {
			STARTING: "Starting",
			DECRYPTING: "Decrypting",
			PROCESSING: "Processing",
			ONLINE: "Online",
			OFFLINE: "Offline",
			QUEUED: "Queued",
			SKIPPED: "Skipped",
			WAITING: "Waiting",
			DOWNLOADING: "Downloading",
			FAILED: "Failed",
			ABORTED: "Aborted",
			FINISHED: "Finished",
			TEMP_OFFLINE: "Temporarily Offline",
			CUSTOM: "Custom",
			UNKNOWN: "Unknown",
		}
		
		def __init__ (self, status):
			self.status = status
		
		@property
		def value (self):
			return self._STATUS_STR[self.status]
		
		def __eq__ (self, other):
			return self.status == other
	
	
	def __init__ (self, data):
		'''
		Constructor
		'''
		Item.__init__ (self, is_link=True)

		self.id = data.fid
		self.url = data.url
		self.name = data.name
		self.plugin = data.plugin
		self.size = data.size
		self.order = data.order
		self.status = Link.Status (data.status)
		self.error = data.error
	
	
	def __repr__ (self):
		return "<Link id: {0}, name: {1}, url: {2}, size: {3}, status: {4}>".format(
			self.id, self.name, self.url, self.size, self.status)