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

from time import time
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
	def __init__ (self, data):
		'''
		Constructor
		'''
		Item.__init__ (self, is_package=True)
		
		self.id = data.pid
		self.name = data.name
		self.folder = data.folder
		self.site = data.site
		self.password = data.password
		self.dest = data.dest
		self.order = data.order
		
		self.links_done = data.linksdone
		self.links_total = len(data.links)
		self.size_done = data.sizedone
		self.size_total = data.sizetotal

		self.links = {link.fid: Link(link) for (link) in data.links}



	@property
	def finished (self):
		return self.links_done == self.links_total


	@property
	def links_online (self):
		states = [Link.Status.ONLINE]
		return sum(1 for link in self.links.itervalues() if link.status in states)


	@property
	def links_offline (self):
		states = [Link.Status.ABORTED, Link.Status.FAILED, Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]
		return sum(1 for link in self.links.itervalues() if link.status in states)

	@property
	def links_downloading (self):
		states = [Link.Status.DOWNLOADING]
		return sum(1 for link in self.links.itervalues() if link.status in states)

	@property
	def links_waiting (self):
		states = [Link.Status.WAITING]
		return sum(1 for link in self.links.itervalues() if link.status in states)
	

	def __update__ (self, val):
		self.id			= val.id
		self.name		= val.name
		self.folder		= val.folder
		self.site		= val.site
		self.password	= val.password
		self.dest		= val.dest
		self.order		= val.order
 
		self.links_done		= val.links_done
		self.links_total	= len(val.links)
		self.size_dont		= val.size_done
		self.size_total		= val.size_total

		for id, link in val.links.iteritems():
			if self.links[id] != link:
				self.links[id].__update__ (link)
	
	
	def __eq__ (self, other):

		for id, link in self.links.iteritems():
			if other.links[id] != link:
				return False

		return (
			self.id == other.id
			and self.name == other.name
			and self.folder == other.folder
			and self.site == other.site
			and self.password == other.password
			and self.dest == other.dest
			and self.order == other.order

			and self.links_done == other.links_done
			and self.links_total == other.links_total
			and self.size_done == other.size_done
			and self.size_total == other.size_total
		)


	def __ne__ (self, other):
		return not (self == other)

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


	@property
	def offline (self):
		return self.status in [Link.Status.ABORTED, Link.Status.FAILED, Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]

	@property
	def active (self):
		return self.status in [Link.Status.DOWNLOADING, Link.Status.WAITING]
	

	def __update__ (self, val):
		self.id		= val.id
		self.url	= val.url
		self.name	= val.name
		self.plugin	= val.plugin
		self.size	= val.size
		self.order	= val.order
		self.status	= val.status
		self.error	= val.error
	
	
	def __eq__ (self, other):
		return (
			self.id == other.id
			and self.url == other.url
			and self.name == other.name
			and self.plugin == other.plugin
			and self.size == other.size
			and self.order == other.order
			and self.status == other.status
			and self.error == other.error
		)

	def __ne__ (self, other):
		return not (self == other)
	
	
	def __repr__ (self):
		return "<Link id: {0}, name: {1}, url: {2}, size: {3}, status: {4}>".format(
			self.id, self.name, self.url, self.size, self.status.value)



class Download (Item):
	'''
	A link currently being downloaded
	'''

	def __init__ (self, data):
		Item.__init__ (self, is_link=True)

		self.id			= data.fid
		self.size		= data.size
		self.speed		= data.speed
		self.bytes_left	= data.bleft
		self.eta		= data.eta
		self.wait_time	= data.wait_until
		self.percent	= data.percent
		self.time_left	= data.wait_until - time()


	@property
	def bytes_transferred (self):
		return self.size - self.bytes_left
	

	def __update__ (self, val):
		self.id			= val.id
		self.size		= val.size
		self.speed		= val.speed
		self.bytes_left	= val.bytes_left
		self.eta		= val.eta
		self.wait_time	= val.wait_time
		self.percent	= val.percent
		self.time_left	= val.time_left

	
	def __eq__ (self, other):
		return (
			self.id == other.id
			and self.size == other.size
			and self.speed == other.speed
			and self.bytes_left == other.bytes_left
			and self.eta == other.eta
			and self.wait_time == other.wait_time
			and self.percent == other.percent
			and self.time_left == other.time_left
		)

	def __ne__ (self, other):
		return not (self == other)
	
	
	def __repr__ (self):
		return "<Download id: {0}, size: {1}, speed: {2}, bytes_left: {3}, eta: {4}, wait_time: {5}>".format(
			self.id, self.size, self.speed, self.bytes_left, self.eta, self.wait_time)