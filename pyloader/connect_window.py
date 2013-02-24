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

from pkg_resources import Requirement, resource_filename
from gi.repository import Gtk, Gio


class ConnectWindow (object):
	'''
	The connection window
	'''


	def __init__ (self, client):
		'''
		Constructor
		'''
		self.client = client

		# load the application settings
		self.settings = Gio.Settings.new ("org.pyLoader.connection")
		
		# load the ui
		filename = resource_filename (Requirement.parse ("pyloader"), "pyloader/ui/login.xml")
		builder = Gtk.Builder()
		builder.add_from_file (filename)
		
		self.window = builder.get_object ("login_window")
		connect_button = builder.get_object ("connect")
		
		self.host = builder.get_object ("host")
		self.port = builder.get_object ("port")
		self.username = builder.get_object ("username")
		self.password = builder.get_object ("password")
		self.autoconnect = builder.get_object ("autoconnect")
		
		connect_button.connect ("clicked", self.__on_connect_click)

		self.host.set_text (self.settings.get_string ("host"))
		self.port.set_value (self.settings.get_uint ("port"))
		self.autoconnect.set_active (self.settings.get_boolean ("autoconnect"))
	
	
	def run (self):
		'''
		Open the dialog and wait for a response
		'''
		return self.window.run()
	
	def hide (self):
		'''
		Hide the dialog window
		'''
		return self.window.hide()

	@property
	def auto_connect (self):
		return self.autoconnect.get_active()


	def connect (self):
		# get connection details
		host = self.host.get_text()
		port = self.port.get_value_as_int()
		username = self.username.get_text()
		password = self.password.get_text()

		return self.client.connect (host, port, username, password)
	
	
	def __on_connect_click (self, button):
		if self.connect():
			self.settings.set_string ("host", self.host.get_text())
			self.settings.set_uint ("port", self.port.get_value_as_int())
			self.settings.set_boolean ("autoconnect", self.autoconnect.get_active())

			self.window.response (Gtk.ResponseType.OK)