#
#    Copyright 2012 Goran Sterjov
#    This file is part of pyLoadGtk.
#
#    pyLoadGtk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyLoadGtk is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pyLoadGtk.  If not, see <http://www.gnu.org/licenses/>.
#

from gi.repository import Gtk, GLib

from server import Server
from login import LoginWindow
from captcha import CaptchaWindow
from queue import Queue


class MainWindow(object):
	'''
	classdocs
	'''


	def __init__(self):
		'''
		Constructor
		'''
		# create the server context
		self.server = Server()
		
		# load the main window
		builder = Gtk.Builder()
		builder.add_from_file ("ui/main.xml")
		
		self.window = builder.get_object ("main_window")
		
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
		
		# create ui components
		self.queue = Queue (builder, self.server)
		self.login_window = LoginWindow (self.server)
		
		# connect to server events
		self.server.queue_changed += self.__on_queue_changed
		self.server.speed_changed += self.__on_speed_changed
		
		self.server.package_added += self.__on_package_added
		self.server.package_removed += self.__on_package_removed
		
		# show main window
		self.window.show_all()
	
	
	def __status_update(self):
		# captcha status
		if self.server.check_captcha_waiting():
			print self.server.get_captcha()
		
		# server status
		status = self.server.get_status()
		self.queue_status.set_text("%d/%d" % (status.queue, status.total))
		self.speed_status.set_text("%s/s" % self.queue.format_bytes(status.speed))
		
		self.queue.update_status(self.server)
		
		self.server.process_pending_jobs()
		
		return True
	
	
	def __on_connect_clicked(self, button):
		self.show_login()
	
	
	def __on_start_clicked(self, button):
		self.server.start()
	
	
	def __on_stop_clicked(self, button):
		self.server.stop()
	
	
	def __on_check_clicked(self, button):
		self.queue.check_all_online(self.server)
	
	
	def show_login (self):
		response = self.login_window.run()
		
		if response == Gtk.ResponseType.OK:
			self.load_server_details()
			#self.queue.load_queue(self.server)
			
			#self.__status_update()
			#GLib.timeout_add(500, self.__status_update)
			
			self.server.poll()
			GLib.timeout_add (500, self.server.poll)
		
		self.login_window.hide()
	
	
	def load_server_details (self):
		space = self.queue.format_bytes (self.server.get_free_space())
		self.free_space.set_text (space)
		
		self.server_version.set_text ("v%s" % self.server.get_version())
		self.server_status.set_text (self.server.get_host())
		self.server_status_image.set_from_stock (Gtk.STOCK_YES, Gtk.IconSize.MENU)
	
	
	def __on_queue_changed (self, queue, total):
		self.queue_status.set_text ("%d/%d" % (queue, total))
	
	
	def __on_speed_changed (self, speed):
		self.speed_status.set_text ("%s/s" % self.queue.format_bytes (speed))
	
	
	def __on_package_added (self, package):
		self.queue.add_package (package)
	
	
	def __on_package_removed (self, package):
		print package.name
	
	
if __name__ == "__main__":
	main_window = MainWindow()
	Gtk.main()
