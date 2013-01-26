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


class Collector (object):
	'''
	The collector queue
	'''

	class Columns:
		(ITEM,
		WAIT_UNTIL) = range(2)


	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		self.collector_tree = builder.get_object ("collector_tree")
		
		# columns
		link = builder.get_object ("collector_link")
		host = builder.get_object ("collector_host")
		
		# create the item store (packages and links)
		self.store = Gtk.TreeStore (Item.__gtype__, int)
		self.collector_tree.set_model (self.store)
		
		area = link.get_area()
		area.set_orientation (Gtk.Orientation.VERTICAL)
		
		# create renderers
		name_renderer = Gtk.CellRendererText()
		status_renderer = Gtk.CellRendererText()
		host_renderer = Gtk.CellRendererText()
		
		# set column renderers
		link.pack_start (name_renderer, True)
		link.pack_start (status_renderer, True)
		host.pack_start (host_renderer, True)
		
		link.set_cell_data_func (name_renderer, self.__render_name)
		link.set_cell_data_func (status_renderer, self.__render_status)
		host.set_cell_data_func (host_renderer, self.__render_host)
		
		
		# get colours
		path = Gtk.WidgetPath()
		path.append_type (Gtk.WindowType)
		
		self.package_ctx = Gtk.StyleContext()
		self.package_ctx.set_path (path)
		self.package_ctx.add_class (Gtk.STYLE_CLASS_INFO)
		
		
		# connect to server events
		client.on_collector_added += self.__on_collector_added
		client.on_link_check += self.__on_link_check



	def check_all_items (self):
		'''
		Check the online status of all links in the collector
		'''
		links = []

		for row in self.store:
			package = row[0]

			for link in package.links:
				links.append (link)

		self.client.check_online_status (links)
	
	
	def __set_cell_background (self, cell, item):
		'''
		Sets the cell background color based on the item type and status
		'''
		cell.set_property ("cell-background-set", False)
		
		# packages
		if item.is_package:
			if item.links_online == item.links_total:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.4))
			else:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
			
			cell.set_property ("cell-background-set", True)
		
		# links
		if item.is_link:
			if item.status == Link.Status.ONLINE:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.status in [Link.Status.WAITING]:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 1, 0, 0.5))
				cell.set_property ("cell-background-set", True)
	
	
	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Collector.Columns.ITEM]
		
		# render as a package
		if item.is_package:
			cell.set_property ("markup", "<b>{0}</b>".format(item.name))
		
		# render as a link
		elif item.is_link:
			# get the link size and assume no bytes have been transfered
			size = utils.format_size (item.size)
			details = "[{0}]".format (size)
			
			# render link details as markup and make it visible
			text = "{0}<small>  -  {1}</small>".format (item.name, details)
			cell.set_property ("markup", text)
			cell.set_property ("visible", True)
		
		self.__set_cell_background (cell, item)
	
	
	def __render_status (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Collector.Columns.ITEM]
		
		# set it to invisible so it doesnt render for packages
		cell.set_property ("visible", False)
		
		if item.is_link:
			# get the state of the link
			text = "<b>{0}</b>".format (item.status.value)
			
			if item.status == Link.Status.WAITING:
				# get the current wait time
				seconds = model[iter][Queue.Columns.WAIT_UNTIL]
				wait_time = utils.format_time (seconds - time())
				
				text += "  -  {0} left".format (wait_time)
			
			elif item.status in [Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				text += "  -  {0}".format (item.error)
			
			# render the status and make it visible
			cell.set_property ("markup", "<small>{0}</small>".format (text))
			cell.set_property ("visible", True)
			
		self.__set_cell_background (cell, item)
	
	
	def __render_host (self, column, cell, model, iter, data):
		item = model[iter][Collector.Columns.ITEM]
		
		if item.is_package:
			cell.set_property ("markup", "<small>{0}/{1} online</small>".format (item.links_online, item.links_total))
		
		elif item.is_link:
			cell.set_property ("markup", "<small>{0}</small>".format (item.plugin))
		
		self.__set_cell_background (cell, item)
	
	
	def __on_collector_added (self, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append (None, [package, 0])
		
		for link in package.links:
			self.store.append (parent, [link, 0])
	

	def __on_link_check (self):
		'''
		Handler to update the status of links being checked
		'''
		self.collector_tree.queue_draw()