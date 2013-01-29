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

from gi.repository import Gtk, GLib, Pango, Gio

import os
import mimetypes
import utils


class DownloadItem (Gtk.HBox):
	'''
	An item in the active downloads bar
	'''

	def __init__ (self, link, status):
		'''
		Constructor
		'''
		Gtk.HBox.__init__ (self, False, 10)

		self.link = link
		self.status = status

		mime, encoding = mimetypes.guess_type (link.name)

		box = Gtk.HBox (False, 10)
		details = Gtk.VBox (True, 0)

		image = Gtk.Image ()
		if mime:
			icon = Gio.content_type_get_icon (mime)
			image.set_from_gicon (icon, Gtk.IconSize.DIALOG)
		else:
			image.set_from_stock (Gtk.STOCK_FILE, Gtk.IconSize.DIALOG)

		self.name = Gtk.Label()
		self.name.set_alignment (0, 0.5)
		self.name.set_ellipsize (Pango.EllipsizeMode.END)
		self.name.set_max_width_chars (25)

		self.progress = Gtk.ProgressBar()

		self.speed = Gtk.Label()
		self.speed.set_alignment (0, 0.5)
		self.speed.set_ellipsize (Pango.EllipsizeMode.END)
		self.speed.set_max_width_chars (25)

		details.pack_start (self.name, False, True, 0)
		details.pack_start (self.progress, False, True, 0)
		details.pack_start (self.speed, False, True, 0)

		self.pack_start (image, False, False, 0)
		self.pack_start (details, True, True, 0)

		self.update()


	def update (self):
		self.name.set_markup ("<small>{0}</small>".format (self.link.name))
		self.progress.set_fraction (self.status.percent / 100.0)
		self.speed.set_markup ("<small>{0}/s</small>".format (utils.format_size(self.status.speed)))



class DownloadBar (object):
	'''
	The active downloads bar
	'''

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		self.items = []

		# load the main download box
		self.downloads = builder.get_object ("downloads")
		
		# connect to server events
		client.on_active_added += self.__on_active_added
		client.on_active_changed += self.__on_active_changed
	
	
	def show_connect_window (self):
		'''
		Display the connect dialog
		'''
		response = self.connect_window.run()
		self.connect_window.hide()
	
	

	def __on_active_added (self, status):
		'''
		Handler to show the current status of a download from the server
		'''
		found_link = None

		for package in self.client._queue_cache.itervalues():
			for link in package.links:
				if link.id == status.id:
					item = DownloadItem (link, status)
					self.items.append (item)

					self.downloads.pack_start (item, False, True, 0)
					self.downloads.show_all()


	def __on_active_changed (self):
		'''
		Handler to update items in the download bar
		'''
		for item in self.items:
			item.update()