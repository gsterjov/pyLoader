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

	class Columns:
		(ITEM,
		SPEED,
		ETA,
		BYTES_LEFT,
		WAIT_UNTIL) = range(5)


	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.queue_tree = builder.get_object ("queue_tree")
		
		# columns
		link = builder.get_object ("queue_link")
		host = builder.get_object ("queue_host")
		
		# create the item store (packages and links)
		self.store = Gtk.TreeStore (Item.__gtype__, int, int, int, int)
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
		client.on_finished_added += self.__on_finished_added
	
	
	
	def __set_cell_background (self, cell, item):
		'''
		Sets the cell background color based on the item type and status
		'''
		cell.set_property ("cell-background-set", False)
		
		# packages
		if item.is_package:
			if item.links_done == item.links_total:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.4))
			else:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.7, 0, 0.4))
			
			cell.set_property ("cell-background-set", True)
		
		# links
		if item.is_link:
			if item.status == Link.Status.FINISHED:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.ABORTED, Link.Status.FAILED, Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.WAITING]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 1, 0, 0.5))
				cell.set_property ("cell-background-set", True)
	
	
	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Queue.Columns.ITEM]
		
		# render as a package
		if item.is_package:
			cell.set_property ("markup", "<b>{0}</b>".format(item.name))
			#text = "<small>{0}/{1}</small>".format(item.links_done, item.links_total)
		
		# render as a link
		elif item.is_link:
			# get the state of the link
			status = "<b>{0}</b>".format (item.status.value)

			# get the link size and assume no bytes have been transfered
			size = utils.format_size (item.size)
			details = "[{0}]".format (size)
			
			# link is downloading
			if item.status == Link.Status.DOWNLOADING:
				# get the current bytes transferred
				bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
				seconds_left = model[iter][Queue.Columns.ETA]

				# get the current speed
				speed = model[iter][Queue.Columns.SPEED]
				speed = utils.format_size (speed)
				
				transfered = utils.format_size (item.size - bytes_left)
				eta = utils.format_time (seconds_left)

				details = "[{0} of {1} at {2}/s]  -  {3}".format (transfered, size, eta)

			# link is pending some action
			elif item.status == Link.Status.WAITING:
				# get the current wait time
				seconds = model[iter][Queue.Columns.WAIT_UNTIL]
				wait_time = utils.format_time (seconds - time())
				
				details = "[{0}]  -  {1} left".format (size, wait_time)
			
			# link has failed
			elif item.status == Link.Status.FAILED:
				details = "[{0}]  -  {1}".format (size, item.error)

			
			# render link details as markup and make it visible
			text = "<small>{0}  -  {1}  -  {2}</small>".format (item.name, status, details)
			cell.set_property ("markup", text)
			cell.set_property ("visible", True)
		
		self.__set_cell_background (cell, item)
	
	
	def __render_status (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Queue.Columns.ITEM]
		
		# set it to invisible so it doesnt render for packages
		cell.set_property ("visible", False)
		
		if item.is_link:
			# get the state of the link
			text = "<b>{0}</b>".format (item.status.value)
			
			if item.status == Link.Status.DOWNLOADING:
				# get the current speed and format it
				speed = model[iter][Queue.Columns.SPEED]
				speed = utils.format_size (speed)
				
				# get current percentage done
				bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
				transferred = item.size - bytes_left
				percent = (float(transferred) / float(item.size)) * 100
				
				text += "  ({0}%)  -  {1}/s".format (int(percent), speed)
			
			elif item.status == Link.Status.WAITING:
				# get the current wait time
				seconds = model[iter][Queue.Columns.WAIT_UNTIL]
				wait_time = utils.format_time (seconds - time())
				
				text += "  -  {0} left".format (wait_time)
			
			elif item.status == Link.Status.FAILED:
				text += "  -  {0}".format (item.error)
			
			# render the status and make it visible
			cell.set_property ("markup", "<small>{0}</small>".format (text))
			cell.set_property ("visible", True)
			
		self.__set_cell_background (cell, item)
	
	
	def __render_progress (self, column, cell, model, iter, data):
		item = model[iter][Queue.Columns.ITEM]
		
		cell.set_property ("visible", False)
		
		if item.is_link and item.status == Link.Status.DOWNLOADING:
			bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
			bytes_transferred = item.size - bytes_left
			percent = (float(bytes_transferred) / float(item.size)) * 100
			
			cell.set_property ("height", 10)
			cell.set_property ("text", "")
			cell.set_property ("value", percent)
			cell.set_property ("visible", True)
	
	
	def __render_host (self, column, cell, model, iter, data):
		item = model[iter][Queue.Columns.ITEM]
		
		if item.is_package:
			cell.set_property ("markup", "<small>{0}/{1} completed</small>".format (item.links_done, item.links_total))
		
		elif item.is_link:
			cell.set_property ("markup", "<small>{0}</small>".format (item.plugin))
		
		self.__set_cell_background (cell, item)
	
	
	
	def __get_link_iter (self, link_id):
		# get root iterator
		package_iter = self.store.get_iter_first()
		
		# get all packages
		while package_iter != None:
			
			# get all links in the package
			link_iter = self.store.iter_children (package_iter)
			
			while link_iter != None:
				
				# return the link iterator if it matches the ID
				link = self.store[link_iter][Queue.Columns.ITEM]
				if link.id == link_id:
					return link_iter
				
				# get the next link in the list
				link_iter = self.store.iter_next (link_iter)
			
			# get the next package in the list
			package_iter = self.store.iter_next (package_iter)
		
		# the link ID wasnt found
		return None
	
	
	def __on_queue_added (self, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append (None, [package, 0, 0, 0, 0])
		
		for link in package.links:
			self.store.append (parent, [link, 0, 0, 0, 0])
	

	def __on_finished_added (self, package):
		'''
		Handler to show newly finished packages from the server
		'''
		parent = self.store.append (None, [package, 0, 0, 0, 0])
		
		for link in package.links:
			self.store.append (parent, [link, 0, 0, 0, 0])