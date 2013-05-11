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
from items import Item, Package, Link
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

		# load the application settings
		self.settings = Gio.Settings.new ("org.pyLoader.queue")

		self.links = Links (builder, client)
		self.tree = builder.get_object ("queue_tree")
		
		# create the item store (packages)
		self.store = Gtk.ListStore (Package.__gtype__)
		self.store.set_sort_func (0, self.__store_compare, None)
		self.tree.set_model (self.store)
		

		# queue columns
		self.order_column		= builder.get_object ("queue_order")
		self.name_column		= builder.get_object ("queue_name")
		self.links_column		= builder.get_object ("queue_links")
		self.size_column		= builder.get_object ("queue_size")
		self.downloaded_column	= builder.get_object ("queue_downloaded")
		self.speed_column		= builder.get_object ("queue_speed")
		self.eta_column			= builder.get_object ("queue_eta")
		self.progress_column	= builder.get_object ("queue_progress")
		
		# create renderers
		order_renderer		= Gtk.CellRendererText()
		name_renderer		= Gtk.CellRendererText()
		links_renderer		= Gtk.CellRendererText()
		size_renderer		= Gtk.CellRendererText()
		downloaded_renderer	= Gtk.CellRendererText()
		speed_renderer		= Gtk.CellRendererText()
		eta_renderer		= Gtk.CellRendererText()
		progress_renderer	= Gtk.CellRendererProgress()
		
		# set column renderers
		self.order_column.pack_start (order_renderer, True)
		self.name_column.pack_start (name_renderer, True)
		self.links_column.pack_start (links_renderer, True)
		self.size_column.pack_start (size_renderer, True)
		self.downloaded_column.pack_start (downloaded_renderer, True)
		self.speed_column.pack_start (speed_renderer, True)
		self.eta_column.pack_start (eta_renderer, True)
		self.progress_column.pack_start (progress_renderer, True)
		
		self.order_column.set_cell_data_func (order_renderer, self.__render_order)
		self.name_column.set_cell_data_func (name_renderer, self.__render_name)
		self.links_column.set_cell_data_func (links_renderer, self.__render_links)
		self.size_column.set_cell_data_func (size_renderer, self.__render_size)
		self.downloaded_column.set_cell_data_func (downloaded_renderer, self.__render_downloaded)
		self.speed_column.set_cell_data_func (speed_renderer, self.__render_speed)
		self.eta_column.set_cell_data_func (eta_renderer, self.__render_eta)
		self.progress_column.set_cell_data_func (progress_renderer, self.__render_progress)


		# connect to ui events
		# self.tree.connect ("button-press-event", self.__on_button_press)

		selection = self.tree.get_selection()
		selection.connect ("changed", self.__on_selection_changed)

		# connect to client property events
		client.on_connected += self.__on_connected

		client.queue.added += self.__on_queue_added
		client.queue.changed += self.__on_queue_changed
		client.downloads.changed += self.__on_downloads_changed


		# load the queue column settings
		self.order_column.set_fixed_width (self.settings.get_uint ("column-order-size"))
		self.name_column.set_fixed_width (self.settings.get_uint ("column-name-size"))
		self.links_column.set_fixed_width (self.settings.get_uint ("column-links-size"))
		self.size_column.set_fixed_width (self.settings.get_uint ("column-size-size"))
		self.downloaded_column.set_fixed_width (self.settings.get_uint ("column-downloaded-size"))
		self.speed_column.set_fixed_width (self.settings.get_uint ("column-speed-size"))
		self.eta_column.set_fixed_width (self.settings.get_uint ("column-eta-size"))
		self.progress_column.set_fixed_width (self.settings.get_uint ("column-progress-size"))


	def save_state (self):
		self.settings.set_uint ("column-order-size", self.order_column.get_width())
		self.settings.set_uint ("column-name-size", self.name_column.get_width())
		self.settings.set_uint ("column-links-size", self.links_column.get_width())
		self.settings.set_uint ("column-size-size", self.size_column.get_width())
		self.settings.set_uint ("column-downloaded-size", self.downloaded_column.get_width())
		self.settings.set_uint ("column-speed-size", self.speed_column.get_width())
		self.settings.set_uint ("column-eta-size", self.eta_column.get_width())
		self.settings.set_uint ("column-progress-size", self.progress_column.get_width())


	def __render_order (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("text", "{0}".format (item.order))


	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("text", item.name)


	def __render_links (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("text", "{0}/{0} completed".format (item.links_done, item.links_total))


	def __render_size (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		total = utils.format_size (item.size_total)
		cell.set_property ("text", total)


	def __render_downloaded (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		if item.size_done > 0:
			total = utils.format_size (item.size_done)
			cell.set_property ("text", total)
		else:
			cell.set_property ("text", "")



	def __render_speed (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		if item.links_downloading:
			speed = 0
			downloads = self.client.downloads.value

			for link in item.links.itervalues():
				if downloads.has_key (link.id):
					speed += downloads[link.id].speed

			speed = utils.format_size (speed)
			cell.set_property ("text", "{0}/s".format (speed))

		else:
			cell.set_property ("text", "")


	def __render_eta (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		# link is active
		if item.links_downloading:
			eta = 0
			downloads = self.client.downloads.value

			for link in item.links.itervalues():
				if downloads.has_key (link.id):
					eta += downloads[link.id].eta

			eta = utils.format_time (eta)
			cell.set_property ("markup", eta)

		# link is waiting
		elif not item.links_downloading and item.links_waiting:
			eta = None
			downloads = self.client.downloads.value

			for link in item.links.itervalues():
				if downloads.has_key (link.id):
					time_left = downloads[link.id].time_left

					if not eta: eta = time_left
					elif time_left < eta: eta = time_left

			eta = eta if eta > 0 else 0
			eta = utils.format_time (eta)
			cell.set_property ("markup", "<small>Waiting - {0}</small>".format (eta))

		# inactive link
		else:
			cell.set_property ("markup", "")
	
	
	def __render_progress (self, column, cell, model, iter, data):
		item = model[iter][0]

		percent = 0
		downloads = self.client.downloads.value

		for link in item.links.itervalues():
			if downloads.has_key (link.id):
				percent += downloads[link.id].percent

			elif link.status == Link.Status.FINISHED:
				percent += 100

		cell.set_property ("value", percent / len(item.links))
	

	def __store_compare (self, model, row1, row2, userdata):
		item1 = model[row1][0]
		item2 = model[row2][0]
		
		if item1.order < item2.order: return -1
		elif item1.order == item2.order: return 0
		else: return 1


	def __on_connected (self):
		self.client.request_queue_update()

	
	def __on_queue_added (self, prop, package):
		'''
		Handler to show newly added packages from the server
		'''
		parent = self.store.append ([package])


	def __on_queue_changed (self, prop, package):
		self.tree.queue_draw()


	def __on_downloads_changed (self, property, value):
		self.tree.queue_draw()



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