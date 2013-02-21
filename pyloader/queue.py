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
		self.client = client

		self.queue_tree = builder.get_object ("queue_tree")

		self.link_menu_failed = builder.get_object ("queue_link_failed")
		self.link_menu_active = builder.get_object ("queue_link_active")

		menu_item_restart = builder.get_object ("queue_link_restart")
		menu_item_abort = builder.get_object ("queue_link_abort")

		# self.menu_item_move = builder.get_object ("queue_package_move")
		# self.menu_item_resume = builder.get_object ("queue_package_resume")
		# self.menu_item_pause = builder.get_object ("queue_package_pause")
		
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

		# connect to ui events
		self.queue_tree.connect ("button-press-event", self.__on_button_press)
		menu_item_restart.connect ("activate", self.__on_restart_link)
		menu_item_abort.connect ("activate", self.__on_abort_link)

		# connect to client property events
		client.queue.added += self.__on_queue_added
		client.queue.changed += self.__on_queue_changed

		client.downloads.added += self.__on_downloads_added
		client.downloads.changed += self.__on_downloads_changed

		client.on_finished_added += self.__on_finished_added
	
	
	
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

			elif item.links_offline > 0:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
				cell.set_property ("cell-background-set", True)
			
			elif item.links_waiting > 0:
				cell.set_property ("cell-background-rgba", Gdk.RGBA(1, 1, 0, 0.5))
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
				remaining = active_link.time_left if active_link.time_left > 0 else 0
				wait_time = utils.format_time (remaining)

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
	
	
	def __on_queue_added (self, prop, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append (None, [package, None])
		
		for link in package.links.itervalues():
			self.store.append (parent, [link, None])


	def __on_queue_changed (self, prop, package):
		self.queue_tree.queue_draw()
	

	def __on_downloads_added (self, prop, download):
		'''
		Handler to show the current status of a download from the server
		'''
		for row in self.store:
			for item in row.iterchildren():
				if item[0].id == download.id:
					item[1] = download


	def __on_downloads_changed (self, prop, download):
		'''
		Handler to refresh the queue tree
		'''
		self.queue_tree.queue_draw()


	def __on_downloads_removed (self, prop, download):
		'''
		Handler to remove downloads no longer active
		'''
		print download
	

	def __on_finished_added (self, package):
		'''
		Handler to show newly finished packages from the server
		'''
		parent = self.store.append (None, [package, None])
		
		for link in package.links.itervalues():
			self.store.append (parent, [link, None])



	def __on_button_press (self, widget, event):
		'''
		Handler to show the popup menu in the queue
		'''
		if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
			# get the current selection to determine which popup to use
			path, column, cell_x, cell_y = self.queue_tree.get_path_at_pos (event.x, event.y)
			iter = self.store.get_iter (path)

			# show the right context
			if iter and self.store[iter][0].is_link:
				link = self.store[iter][0]

				if link.offline:
					self.link_menu_failed.popup (None, None, None, None, event.button, event.time)

				elif link.active:
					self.link_menu_active.popup (None, None, None, None, event.button, event.time)

		return False


	def __on_restart_link (self, userdata):
		'''
		Handler to restart failed links
		'''
		selection = self.queue_tree.get_selection()
		model, iter = selection.get_selected()

		if iter != None:
			link = model[iter][0]
			self.client.restart_link (link)


	def __on_abort_link (self, userdata):
		'''
		Handler to abort active links
		'''
		selection = self.queue_tree.get_selection()
		model, iter = selection.get_selected()

		if iter != None:
			link = model[iter][0]
			self.client.abort_link (link)