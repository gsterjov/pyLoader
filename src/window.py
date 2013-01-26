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

from gi.repository import Gtk, GLib

from client import Client
from connect_window import ConnectWindow
#from captcha import CaptchaWindow
from queue import Queue
from collector import Collector

import utils


class MainWindow (object):
	'''
	The main window
	'''

	def __init__ (self):
		'''
		Constructor
		'''
		self.client = Client()
		
		# load the main window
		builder = Gtk.Builder()
		builder.add_from_file ("ui/main.xml")
		self.window = builder.get_object ("main_window")
		
		# create ui components
		self.queue = Queue (builder, self.client)
		self.collector = Collector (builder, self.client)
		self.connect_window = ConnectWindow (self.client)
		self.connect_window.window.set_transient_for (self.window)
		

		# statusbar
		self.statusbar = builder.get_object ("statusbar")
		self.server_status_image = builder.get_object ("server_status_image")
		self.server_status = builder.get_object ("server_status")
		self.queue_status = builder.get_object ("queue_status")
		self.speed_status = builder.get_object ("speed_status")
		
		# toolbar
		self.connect_button = builder.get_object ("connect")
		self.start_button = builder.get_object ("start")
		self.stop_button = builder.get_object ("stop")
		self.check_button = builder.get_object ("check")
		
		self.free_space = builder.get_object ("free_space")
		self.server_version = builder.get_object ("server_version")
		
		self.state_context = self.statusbar.get_context_id ("Application state")
		
		# connect to ui events
		self.window.connect ("delete-event", Gtk.main_quit)
		self.connect_button.connect ("clicked", self.__on_connect_clicked)
		self.start_button.connect ("clicked", self.__on_start_clicked)
		self.stop_button.connect ("clicked", self.__on_stop_clicked)
		self.check_button.connect ("clicked", self.__on_check_clicked)
		
		# connect to server events
		self.client.on_connected += self.__on_connected
		
		self.client.speed.changed += self.__on_speed_changed
		self.client.links_active.changed += self.__on_links_active_changed
		self.client.links_waiting.changed += self.__on_links_waiting_changed
		
		# show main window
		self.window.show_all()

		self.__load()
	
	
	def show_connect_window (self):
		'''
		Display the connect dialog
		'''
		response = self.connect_window.run()
		self.connect_window.hide()
	

	def __load (self):
		if self.connect_window.auto_connect:
			self.connect_window.connect()
	

	# UI Events
	def __on_connect_clicked (self, button):
		self.show_connect_window()
	
	def __on_start_clicked (self, button):
		self.client.resume()
	
	def __on_stop_clicked (self, button):
		self.client.pause()
	
	def __on_check_clicked (self, button):
		self.collector.check_all_items()
	
	
	# Server events
	def __on_connected (self):
		# display the server details
		self.server_version.set_text ("v{0}".format(self.client.version))
		self.free_space.set_text ("{0}".format(utils.format_size(self.client.free_space)))
		
		self.server_status.set_text (self.client.host)
		self.server_status_image.set_from_stock (Gtk.STOCK_YES, Gtk.IconSize.MENU)
		
		# periodically poll the client for any property changes
		GLib.timeout_add (500, self.client.poll)
	
	
	def __on_links_active_changed (self, prop, value):
		self.queue_status.set_text ("{0}/{1}".format(value, self.client.links_total.value))
	
	def __on_links_waiting_changed (self, prop, value):
		self.queue_status.set_text ("{0}/{1}".format(self.client.links_active.value, value))
	
	def __on_speed_changed (self, prop, speed):
		self.speed_status.set_text ("{0}/s".format(utils.format_size(speed)))
	
	
	
if __name__ == "__main__":
	main_window = MainWindow()
	Gtk.main()
