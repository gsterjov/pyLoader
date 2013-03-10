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
import mimetypes
from gi.repository import Gtk, Gdk, Gio, Pango

import utils
from items import Item, Package
from links import Links


class Queue (object):
	'''
	The download queue
	'''

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		self.links = Links (builder, client)
		self.tree = builder.get_object ("queue_tree")
		
		# create the item store (packages)
		self.store = Gtk.ListStore (Package.__gtype__)
		self.tree.set_model (self.store)
		

		# queue columns
		id = builder.get_object ("queue_id")
		name = builder.get_object ("queue_name")
		progress = builder.get_object ("queue_progress")
		
		# create renderers
		id_renderer = Gtk.CellRendererText()
		name_renderer = Gtk.CellRendererText()
		progress_renderer = Gtk.CellRendererProgress()
		
		# set column renderers
		id.pack_start (id_renderer, True)
		name.pack_start (name_renderer, True)
		progress.pack_start (progress_renderer, True)
		
		id.set_cell_data_func (id_renderer, self.__render_id)
		name.set_cell_data_func (name_renderer, self.__render_name)
		progress.set_cell_data_func (progress_renderer, self.__render_progress)


		# connect to ui events
		self.tree.connect ("button-press-event", self.__on_button_press)

		selection = self.tree.get_selection()
		selection.connect ("changed", self.__on_selection_changed)

		# connect to client property events
		client.queue.added += self.__on_queue_added
		client.queue.changed += self.__on_queue_changed

		# client.downloads.added += self.__on_downloads_added
		# client.downloads.changed += self.__on_downloads_changed

		# client.on_finished_added += self.__on_finished_added
	

	def __render_id (self, column, cell, model, iter, data):
		pass


	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("markup", "<b>{0}</b>".format (item.name))
	
	
	def __render_progress (self, column, cell, model, iter, data):
		item = model[iter][0]
		cell.set_property ("value", item.downloads_percent)
	
	
	def __on_queue_added (self, prop, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append ([package])


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


	def __on_selection_changed (self, selection):
		model, iter = selection.get_selected()
		package = model[iter][0]
		self.links.load (package)