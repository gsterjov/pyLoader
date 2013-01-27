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

import datetime
from time import time
from gi.repository import Gtk, Gdk

import utils
from items import Item, Link


class Queue (object):
	'''
	The download queue
	'''

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.queue_tree = builder.get_object ("queue_tree")
		
		# columns
		link = builder.get_object ("queue_link")
		host = builder.get_object ("queue_host")
		
		# create the item store (packages and links)
		self.store = Gtk.TreeStore (Item.__gtype__, Item.__gtype__)
		self.queue_tree.set_model (self.store)
		
		# create renderers
		name_renderer = Gtk.CellRendererText()
		host_renderer = Gtk.CellRendererText()
		
		# set column renderers
		link.pack_start (name_renderer, True)
		host.pack_start (host_renderer, True)
		
		link.set_cell_data_func (name_renderer, self.__render_name)
		host.set_cell_data_func (host_renderer, self.__render_host)

		# connect to server events
		client.on_queue_added += self.__on_queue_added
		client.on_active_added += self.__on_active_added
		client.on_finished_added += self.__on_finished_added
		client.on_active_changed += self.__on_active_changed
	
	
	
	def __set_cell_background (self, cell, item):
		'''
		Sets the cell background color based on the item type and status
		'''
		cell.set_property ("cell-background-set", False)
		
		# packages
		if item.is_package:
			if item.links_done == item.links_total:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.3))

			elif item.links_downloading > 0:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0, 0, 1, 0.1))
				cell.set_property ("cell-background-set", True)
		
		# links
		if item.is_link:
			if item.status == Link.Status.FINISHED:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.3))
				cell.set_property ("cell-background-set", True)

			elif item.status == Link.Status.DOWNLOADING:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0, 0, 1, 0.1))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.ABORTED, Link.Status.FAILED, Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.WAITING]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 1, 0, 0.5))
				cell.set_property ("cell-background-set", True)
	
	
	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		
		# render as a package
		if item.is_package:
			cell.set_property ("markup", "<b>{0}</b>".format(item.name))
		
		# render as a link
		elif item.is_link:
			active_link = model[iter][1]
			
			# get the state of the link
			status = "<b>{0}</b>".format (item.status.value)

			# get the link size and assume no bytes have been transfered
			size = utils.format_size (item.size)
			details = "[{0}]".format (size)
			
			# link is downloading
			if active_link and item.status == Link.Status.DOWNLOADING:
				# get downloading details
				speed = utils.format_size (active_link.speed)
				transfered = utils.format_size (active_link.bytes_transferred)
				eta = utils.format_time (active_link.eta)

				details = "[{0} of {1} at {2}/s]  -  {3}".format (transfered, size, speed, eta)

			# link is pending some action
			elif active_link and item.status == Link.Status.WAITING:
				# get the current wait time
				wait_time = utils.format_time (active_link.wait_time - time())
				details = "[{0}]  -  {1} left".format (size, wait_time)
			
			# link has failed
			elif item.status == Link.Status.FAILED:
				details = "[{0}]  -  {1}".format (size, item.error)

			
			# render link details as markup and make it visible
			text = "<small>{0}  -  {1}  -  {2}</small>".format (item.name, status, details)
			cell.set_property ("markup", text)
			cell.set_property ("visible", True)
		
		self.__set_cell_background (cell, item)
	
	
	def __render_host (self, column, cell, model, iter, data):
		item = model[iter][0]
		
		if item.is_package:
			cell.set_property ("markup", "<small>{0}/{1} completed</small>".format (item.links_done, item.links_total))
		
		elif item.is_link:
			cell.set_property ("markup", "<small>{0}</small>".format (item.plugin))
		
		self.__set_cell_background (cell, item)
	
	
	def __on_queue_added (self, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append (None, [package, None])
		
		for link in package.links:
			self.store.append (parent, [link, None])
	

	def __on_active_added (self, link):
		'''
		Handler to show the current status of a download from the server
		'''
		for row in self.store:
			for item in row.iterchildren():
				if item[0].id == link.id:
					item[1] = link
	

	def __on_finished_added (self, package):
		'''
		Handler to show newly finished packages from the server
		'''
		parent = self.store.append (None, [package, None])
		
		for link in package.links:
			self.store.append (parent, [link, None])
	

	def __on_active_changed (self):
		'''
		Handler to refresh the queue tree
		'''
		self.queue_tree.queue_draw()