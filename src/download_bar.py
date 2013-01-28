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

import mimetypes
import utils


class DownloadBar (object):
	'''
	The active downloads bar
	'''

	def __init__ (self, builder, client):
		'''
		Constructor
		'''
		self.client = client

		# load the main download box
		self.downloads = builder.get_object ("downloads")
		
		# connect to server events
		client.on_active_added += self.__on_active_added
	
	
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
					found_link = link
		
		mime, encoding = mimetypes.guess_type (found_link.name)
		icon = Gio.content_type_get_icon (mime)

		box = Gtk.HBox (False, 10)
		details = Gtk.VBox (True, 0)

		image = Gtk.Image ()
		image.set_from_gicon (icon, Gtk.IconSize.DIALOG)

		label = Gtk.Label()
		label.set_markup ("<small>{0}</small>".format (found_link.name))
		label.set_alignment (0, 0.5)
		label.set_ellipsize (Pango.EllipsizeMode.END)
		label.set_max_width_chars (25)

		progress = Gtk.ProgressBar()
		progress.set_fraction (status.percent / 100.0)

		speed = Gtk.Label()
		speed.set_markup ("<small>{0}/s</small>".format (utils.format_size(status.speed)))
		speed.set_alignment (0, 0.5)
		speed.set_ellipsize (Pango.EllipsizeMode.END)
		speed.set_max_width_chars (25)

		details.pack_start (label, False, True, 0)
		details.pack_start (progress, False, True, 0)
		details.pack_start (speed, False, True, 0)

		box.pack_start (image, False, False, 0)
		box.pack_start (details, True, True, 0)

		self.downloads.pack_start (box, False, True, 0)
		self.downloads.show_all()