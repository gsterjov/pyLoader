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

from gi.repository import Gtk


class LoginWindow (object):
	'''
	classdocs
	'''


	def __init__ (self, server):
		'''
		Constructor
		'''
		self.server = server
		
		builder = Gtk.Builder()
		builder.add_from_file ("ui/login.xml")
		
		self.window = builder.get_object ("login_window")
		connect_button = builder.get_object ("connect")
		
		self.host = builder.get_object ("host")
		self.port = builder.get_object ("port")
		self.username = builder.get_object ("username")
		self.password = builder.get_object ("password")
		
		connect_button.connect ("clicked", self.login)
	
	
	def run (self):
		return self.window.run()
	
	def hide (self):
		return self.window.hide()
	
	
	def login (self, button):
		# get connection details
		host = self.host.get_text()
		port = self.port.get_value_as_int()
		username = self.username.get_text()
		password = self.password.get_text()
		
		self.server.connect (host, port, username, password)
		self.window.response(Gtk.ResponseType.OK)
