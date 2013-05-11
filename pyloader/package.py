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


class Package (GObject.Object):
	'''
	A package contains links to be downloaded within the same folder
	'''
	def __init__ (self, data):
		'''
		Constructor
		'''
		GObject.Object.__init__ (self)

		self.parse (data)
		
		# self.id = data.pid
		# self.name = data.name
		# self.folder = data.folder
		# self.site = data.site
		# self.password = data.password
		# self.dest = data.dest
		# self.order = data.order
		
		# self.links_done = data.linksdone
		# self.links_total = len(data.links)
		# self.size_done = data.sizedone
		# self.size_total = data.sizetotal

		# self.links = {link.fid: Link(link) for (link) in data.links}



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
	

	def parse (self, data):
		self.id			= data["pid"]
		self.name		= data["name"]
		self.folder		= data["folder"]
		self.site		= data["site"]
		self.password	= data["password"]
		self.order		= data["packageorder"]
		self.added		= data["added"]
		self.comment	= data["comment"]
		self.owner		= data["owner"]
		self.status		= data["status"]
		self.tags		= data["tags"]

		# stats
		self.links_done		= data["stats"]["linksdone"]
		self.links_total	= data["stats"]["linkstotal"]
		self.size_done		= data["stats"]["sizedone"]
		self.size_total		= data["stats"]["sizetotal"]



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