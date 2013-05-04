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

import logging

from pkg_resources import Requirement, resource_filename
from gi.repository import Gtk, Gdk, GLib, Gio, Notify

from client import Client
from connect_window import ConnectWindow
from captcha import CaptchaWindow
from queue import Queue
from collector import Collector
from download_bar import DownloadBar

import utils


class MainWindow (object):
	'''
	The main window
	'''

	def __init__ (self, application):
		'''
		Constructor
		'''
		self.application = application
		self.client = Client()

		# load the application settings
		self.settings = Gio.Settings.new ("org.pyLoader.ui")
		
		# load the main window
		filename = resource_filename (Requirement.parse ("pyloader"), "pyloader/ui/main.xml")
		builder = Gtk.Builder()
		builder.add_from_file (filename)
		self.window = builder.get_object ("main_window")

		# set up notification
		Notify.init ("pyLoader")
		self.notification = Notify.Notification.new ("New Captcha", "Please fill out the follwing captcha", "dialog-question")

		self.notification.add_action ("show-captcha", "Enter Captcha", self.__on_show_captcha, None, None)
		self.notification.set_hint ("sound-name", GLib.Variant("s", "dialog-question"))
		self.notification.set_hint ("desktop-entry", GLib.Variant("s", "empathy"))
		
		# create ui components
		self.queue = Queue (builder, self.client)
		self.collector = Collector (builder, self.client)
		self.download_bar = DownloadBar (builder, self.client)


		# connect window
		self.connect_window = ConnectWindow (self.client)
		self.connect_window.window.set_transient_for (self.window)

		# captcha window
		self.captcha_window = CaptchaWindow()
		self.captcha_window.window.set_transient_for (self.window)


		# statusbar
		self.statusbar = builder.get_object ("statusbar")
		self.server_status_image = builder.get_object ("server_status_image")
		self.server_status = builder.get_object ("server_status")
		self.queue_status = builder.get_object ("queue_status")
		self.speed_status = builder.get_object ("speed_status")
		self.space_status = builder.get_object ("space_status")
		
		# toolbar
		self.connect_button = builder.get_object ("connect")
		self.start_button = builder.get_object ("start")
		self.stop_button = builder.get_object ("stop")
		self.check_button = builder.get_object ("check")
		self.clear_button = builder.get_object ("clear")
		
		self.state_context = self.statusbar.get_context_id ("Application state")
		
		# connect to ui events
		self.window.connect ("delete-event", self.__on_close)
		self.window.connect ("window-state-event", self.__on_window_state)

		self.connect_button.connect ("clicked", self.__on_connect_clicked)
		self.start_button.connect ("clicked", self.__on_start_clicked)
		self.stop_button.connect ("clicked", self.__on_stop_clicked)
		self.check_button.connect ("clicked", self.__on_check_clicked)
		self.clear_button.connect ("clicked", self.__on_clear_clicked)
		
		# connect to server events
		self.client.on_connected += self.__on_connected
		
		self.client.speed.changed += self.__on_speed_changed
		self.client.links_active.changed += self.__on_links_active_changed
		self.client.links_waiting.changed += self.__on_links_waiting_changed

		self.client.captchas.added += self.__on_captcha_added

		# show main window
		w, h = self.settings.get_value ("window-size")
		self.window.resize (w, h)

		if self.settings.get_value ("maximised"):
			self.window.maximize()

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


	def __on_close (self, window, event):
		try:
			w, h = window.get_size()
			self.settings.set_value ("window-size", GLib.Variant ('ai', [w, h]))

			self.queue.save_state()

			from twisted.internet import reactor
			reactor.stop()

		except Exception as e:
			from twisted.internet import reactor
			reactor.stop()
			raise e


	def __on_window_state (self, window, event):
		gdk_window = window.get_window()
		if gdk_window:
			maximised = gdk_window.get_state() & Gdk.WindowState.MAXIMIZED == Gdk.WindowState.MAXIMIZED
			self.settings.set_boolean ("maximised", maximised)
	

	# UI Events
	def __on_connect_clicked (self, button):
		self.show_connect_window()
	
	def __on_start_clicked (self, button):
		self.client.resume()
	
	def __on_stop_clicked (self, button):
		self.client.pause()
	
	def __on_check_clicked (self, button):
		self.collector.check_all_items()
	
	def __on_clear_clicked (self, button):
		self.client.clear_finished()
	
	
	# Server events
	def __on_connected (self):
		print self.client.version
		# display the server details
		# self.space_status.set_text ("{0}".format(utils.format_size(self.client.free_space)))
		
		# self.server_status.set_text (self.client.host)
		# self.server_status_image.set_from_stock (Gtk.STOCK_YES, Gtk.IconSize.MENU)

		# self.start_button.set_sensitive (self.client.paused)
		# self.stop_button.set_sensitive (not self.client.paused)
		
		# periodically poll the client for any property changes
		# GLib.timeout_add (500, self.client.poll)
		pass
	
	
	def __on_links_active_changed (self, prop, value):
		self.queue_status.set_text ("{0}/{1}".format(value, self.client.links_total.value))
	
	def __on_links_waiting_changed (self, prop, value):
		self.queue_status.set_text ("{0}/{1}".format(self.client.links_active.value, value))
	
	def __on_speed_changed (self, prop, speed):
		self.speed_status.set_text ("{0}/s".format(utils.format_size(speed)))
	

	def __on_captcha_added (self, prop, captcha):
		pixbuf = utils.base64_to_pixbuf (captcha.data)

		self.notification.set_image_from_pixbuf (pixbuf)
		self.notification.show()

		self.captcha_window.load (pixbuf)

		response = self.captcha_window.run()
		self.captcha_window.hide()

		if response == 0:
			self.client.answer_captcha (captcha, self.captcha_window.answer)


	def __on_show_captcha (self, notification, action, userdata):
		self.window.present()
