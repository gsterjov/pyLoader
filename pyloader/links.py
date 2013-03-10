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


class Links (object):
	'''
	The download queue
	'''

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		self.tree = builder.get_object ("link_tree")
		self.title = builder.get_object ("links_selected_package")

		self.menu_failed = builder.get_object ("menu_link_failed")
		self.menu_active = builder.get_object ("menu_link_active")

		menu_item_restart = builder.get_object ("menu_link_restart")
		menu_item_abort = builder.get_object ("menu_link_abort")

		# self.menu_item_move = builder.get_object ("queue_package_move")
		# self.menu_item_resume = builder.get_object ("queue_package_resume")
		# self.menu_item_pause = builder.get_object ("queue_package_pause")
		
		# create the item store (packages)
		self.store = Gtk.ListStore (Link.__gtype__)
		self.tree.set_model (self.store)
		

		# queue columns
		icon_column		= builder.get_object ("links_icon")
		main_column		= builder.get_object ("links_main")
		status_column	= builder.get_object ("links_status")

		main_column.get_area().set_orientation (Gtk.Orientation.VERTICAL)
		
		# create renderers
		name_renderer		= Gtk.CellRendererText()
		details_renderer	= Gtk.CellRendererText()
		plugin_renderer		= Gtk.CellRendererText()
		status_renderer		= Gtk.CellRendererText()
		progress_renderer	= Gtk.CellRendererProgress()
		icon_renderer		= Gtk.CellRendererPixbuf()
		status_icon_renderer = Gtk.CellRendererPixbuf()
		
		# set column renderers
		icon_column.pack_start (icon_renderer, True)
		main_column.pack_start (name_renderer, True)
		main_column.pack_start (progress_renderer, True)
		main_column.pack_start (details_renderer, True)
		status_column.pack_start (status_icon_renderer, True)
		status_column.pack_start (status_renderer, True)
		
		icon_column.set_cell_data_func (icon_renderer, self.__render_icon)
		main_column.set_cell_data_func (name_renderer, self.__render_name)
		main_column.set_cell_data_func (details_renderer, self.__render_details)
		main_column.set_cell_data_func (progress_renderer, self.__render_progress)
		status_column.set_cell_data_func (status_icon_renderer, self.__render_status_icon)
		status_column.set_cell_data_func (status_renderer, self.__render_status)


		# connect to ui events
		self.tree.connect ("button-press-event", self.__on_button_press)
		menu_item_restart.connect ("activate", self.__on_restart_link)
		menu_item_abort.connect ("activate", self.__on_abort_link)

		# connect to server events
		self.client.downloads.changed += self.__on_downloads_changed


		self.icon_theme = Gtk.IconTheme.get_default()
	


	def load (self, package):
		'''
		Load the links in the package into the link tree
		'''
		self.store.clear()

		for link in package.links.itervalues():
			self.store.append ([link])

		self.title.set_markup ("<big><b>{0}</b></big>".format (package.name))


	def __render_icon (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		pixbuf = None

		mime, encoding = mimetypes.guess_type (item.name)

		if mime:
			icon = Gio.content_type_get_icon (mime)
			icon_info = self.icon_theme.choose_icon (icon.get_names(), 48, 0)
			if icon_info:
				pixbuf = icon_info.load_icon()
		
		if pixbuf:
			cell.set_property ("pixbuf", pixbuf)
		else:
			cell.set_property ("stock-id", Gtk.STOCK_FILE)
			cell.set_property ("stock-size", Gtk.IconSize.DIALOG)


	def __render_status_icon (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		if item.status == Link.Status.FINISHED:
			cell.set_property ("stock-id", Gtk.STOCK_APPLY)

		elif item.offline:
			cell.set_property ("stock-id", Gtk.STOCK_DIALOG_ERROR)

		cell.set_property ("stock-size", Gtk.IconSize.BUTTON)


	def __render_name (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]

		if item.status == Link.Status.FINISHED:
			cell.set_property ("markup", item.name)
		else:
			cell.set_property ("markup", "{0} - <small>{1}</small>".format (item.name, item.url))

		
		# # render as a link
		# elif item.is_link:
		# 	active_link = model[iter][1]
			
		# 	# get the state of the link
		# 	status = "<b>{0}</b>".format (item.status.value)

		# 	# get the link size and assume no bytes have been transfered
		# 	size = utils.format_size (item.size)
		# 	details = "[{0}]".format (size)
			
		# 	# link is downloading
		# 	if active_link and item.status == Link.Status.DOWNLOADING:
		# 		# get downloading details
		# 		speed = utils.format_size (active_link.speed)
		# 		transfered = utils.format_size (active_link.bytes_transferred)
		# 		eta = utils.format_time (active_link.eta)

		# 		details = "[{0} of {1} at {2}/s]  -  {3}".format (transfered, size, speed, eta)

		# 	# link is pending some action
		# 	elif active_link and item.status == Link.Status.WAITING:
		# 		# get the current wait time
		# 		remaining = active_link.time_left if active_link.time_left > 0 else 0
		# 		wait_time = utils.format_time (remaining)

		# 		details = "[{0}]  -  {1} left".format (size, wait_time)
			
		# 	# link has failed
		# 	elif item.status == Link.Status.FAILED:
		# 		details = "[{0}]  -  {1}".format (size, item.error)

			
		# 	# render link details as markup and make it visible
		# 	text = "<small>{0}  -  {1}  -  {2}</small>".format (item.name, status, details)
		# 	cell.set_property ("markup", text)
		# 	cell.set_property ("visible", True)
		
		# self.__set_cell_background (cell, item)


	def __render_details (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		downloads = self.client.downloads.value
		text = ""

		if downloads.has_key (item.id):
			download = downloads[item.id]

			speed = utils.format_size (download.speed)
			eta = utils.format_time (download.eta)
			size = utils.format_size (download.size)
			downloaded = utils.format_size (download.bytes_transferred)

			cell.set_property ("markup", "<small><b>{0}</b> of <b>{1}</b> downloaded  @ <b>{2}/s</b>  with {3} remaining</small>".format (downloaded, size, speed, eta))

		elif item.status == Link.Status.FINISHED:
			size = utils.format_size (item.size)
			cell.set_property ("markup", "<small>{0} downloaded</small>".format (size))

		else:
			text = "<b>{0}</b>".format (item.error) if item.error else ""
			cell.set_property ("markup", "<small>{0}</small>".format (text))
	
	
	def __render_progress (self, column, cell, model, iter, data):
		item = model[iter][0]
		downloads = self.client.downloads.value
		percent = 0

		if downloads.has_key (item.id):
			download = downloads[item.id]
			percent = download.percent

		cell.set_property ("text", "")
		cell.set_property ("height", 10)

		if item.active:
			cell.set_property ("value", percent)
			cell.set_visible (True)
		else:
			cell.set_visible (False)


	def __render_plugin (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("markup", "<small>{0}</small>".format (item.plugin))


	def __render_status (self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][0]
		cell.set_property ("markup", "<small>{0}</small>".format (item.status.value))



	def __on_downloads_changed (self, property, value):
		self.tree.queue_draw()



	def __on_button_press (self, widget, event):
		'''
		Handler to show the popup menu in the queue
		'''
		if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
			# get the current selection to determine which popup to use
			path, column, cell_x, cell_y = self.tree.get_path_at_pos (event.x, event.y)
			iter = self.store.get_iter (path)

			if iter:
				# show the right context
				link = self.store[iter][0]

				if link.offline:
					self.menu_failed.popup (None, None, None, None, event.button, event.time)

				elif link.active:
					self.menu_active.popup (None, None, None, None, event.button, event.time)

		return False


	def __on_restart_link (self, userdata):
		'''
		Handler to restart failed links
		'''
		selection = self.tree.get_selection()
		model, iter = selection.get_selected()

		if iter != None:
			link = model[iter][0]
			self.client.restart_link (link)


	def __on_abort_link (self, userdata):
		'''
		Handler to abort active links
		'''
		selection = self.tree.get_selection()
		model, iter = selection.get_selected()

		if iter != None:
			link = model[iter][0]
			self.client.abort_link (link)