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

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		self.collector_tree = builder.get_object ("collector_tree")
		self.package_menu = builder.get_object ("collector_package_menu")

		menu_item_add = builder.get_object ("collector_package_add")
		
		# columns
		link = builder.get_object ("collector_link")
		host = builder.get_object ("collector_host")
		
		# create the item store (packages and links)
		self.store = Gtk.TreeStore (Item.__gtype__)
		self.collector_tree.set_model (self.store)
		
		# create renderers
		name_renderer = Gtk.CellRendererText()
		host_renderer = Gtk.CellRendererText()
		
		# set column renderers
		link.pack_start (name_renderer, True)
		host.pack_start (host_renderer, True)
		
		link.set_cell_data_func (name_renderer, self.__render_name)
		host.set_cell_data_func (host_renderer, self.__render_host)

		# connect to ui events
		self.collector_tree.connect ("button-press-event", self.__on_button_press)
		menu_item_add.connect ("activate", self.__on_add_to_queue)

		# connect to server events
		client.on_collector_added += self.__on_collector_added
		client.on_collector_removed += self.__on_collector_removed
		client.on_link_checked += self.__on_link_checked



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

			elif item.links_offline > 0:
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
	
	
	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		
		# render as a package
		if item.is_package:
			cell.set_property ("markup", "<b>{0}</b>".format(item.name))
		
		# render as a link
		elif item.is_link:
			# get the state of the link
			status = "<b>{0}</b>".format (item.status.value)

			# get the link size and assume no bytes have been transfered
			size = utils.format_size (item.size)
			details = "[{0}]".format (size)

			if item.status in [Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				details = item.error
			
			# render link details as markup and make it visible
			text = "<small>{0}  -  {1}  -  {2}</small>".format (item.name, status, details)
			cell.set_property ("markup", text)
			cell.set_property ("visible", True)
		
		self.__set_cell_background (cell, item)
	

	def __render_host (self, column, cell, model, iter, data):
		item = model[iter][0]
		
		if item.is_package:
			cell.set_property ("markup", "<small>{0}/{1} online</small>".format (item.links_online, item.links_total))
		
		elif item.is_link:
			cell.set_property ("markup", "<small>{0}</small>".format (item.plugin))
		
		self.__set_cell_background (cell, item)
	
	
	def __on_collector_added (self, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append (None, [package])
		
		for link in package.links:
			self.store.append (parent, [link])
	
	
	def __on_collector_removed (self, package):
		'''
		Handler to removed packages from the server
		'''
		iters = []

		for row in self.store:
			if package.id == row[0].id:
				iters.append (row.iter)

		for iter in iters:
			self.store.remove (iter)


	def __on_link_checked (self):
		'''
		Handler to update the status of links being checked
		'''
		self.collector_tree.queue_draw()



	def __on_button_press (self, widget, event):
		'''
		Handler to show the popup menu in the collector
		'''
		if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
			# get the current selection to determine which popup to use
			selection = self.collector_tree.get_selection()
			model, iter = selection.get_selected()

			if model[iter][0].is_package:
				self.package_menu.popup (None, None, None, None, event.button, event.time)

		return False


	def __on_add_to_queue (self, userdata):
		'''
		Handler to move items in the collector to the queue
		'''
		selection = self.collector_tree.get_selection()
		model, iter = selection.get_selected()

		if iter != None:
			package = model[iter][0]
			self.client.queue_package (package)