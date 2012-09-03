#
#    Copyright 2012 Goran Sterjov
#    This file is part of pyLoadGtk.
#
#    pyLoadGtk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyLoadGtk is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pyLoadGtk.  If not, see <http://www.gnu.org/licenses/>.
#

from gi.repository import GObject
from module.remote.thriftbackend import ThriftClient


class Item(GObject.Object):
	'''
	classdocs
	'''
	
	def __init__(self, is_package=False, is_link=False):
		'''
		Constructor
		'''
		GObject.Object.__init__(self)
		
		self.is_package = is_package
		self.is_link = is_link



class Package(Item):
	'''
	classdocs
	'''

	def __init__(self, client, data):
		'''
		Constructor
		'''
		Item.__init__(self, is_package=True)
		
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
		
		self.update_links()
	
	
	def update_links(self):
		self.links = []
		
		data = self.client.getPackageData(self.id)
		
		for link in data.links:
			self.links.append(Link(self.client, link))



class Link(Item):
	'''
	classdocs
	'''

	class Status(object):
		'''
		classdocs
		'''
		STARTING		= ThriftClient.DownloadStatus.Starting
		DECRYPTING		= ThriftClient.DownloadStatus.Decrypting
		PROCESSING		= ThriftClient.DownloadStatus.Processing
		ONLINE			= ThriftClient.DownloadStatus.Online
		OFFLINE			= ThriftClient.DownloadStatus.Offline
		QUEUED			= ThriftClient.DownloadStatus.Queued
		SKIPPED			= ThriftClient.DownloadStatus.Skipped
		WAITING			= ThriftClient.DownloadStatus.Waiting
		DOWNLOADING		= ThriftClient.DownloadStatus.Downloading
		FAILED			= ThriftClient.DownloadStatus.Failed
		ABORTED			= ThriftClient.DownloadStatus.Aborted
		FINISHED		= ThriftClient.DownloadStatus.Finished
		TEMP_OFFLINE	= ThriftClient.DownloadStatus.TempOffline
		CUSTOM			= ThriftClient.DownloadStatus.Custom
		UNKNOWN			= ThriftClient.DownloadStatus.Unknown


	def __init__(self, client, data):
		'''
		Constructor
		'''
		Item.__init__(self, is_link=True)
		
		self.client = client
		
		self.id = data.fid
		self.url = data.url
		self.name = data.name
		self.plugin = data.plugin
		self.size = data.size
		self.order = data.order
		self.status = data.status
		self.error = data.error
