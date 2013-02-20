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

from pkg_resources import Requirement, resource_filename
from gi.repository import Gtk


class CaptchaWindow(object):
	'''
	classdocs
	'''


	def __init__ (self):
		'''
		Constructor
		'''
		filename = resource_filename (Requirement.parse ("pyloader"), "pyloader/ui/captcha_notify.xml")
		builder = Gtk.Builder()
		builder.add_from_file (filename)
		
		self.window = builder.get_object ("captcha_window")
		submit = builder.get_object ("submit")
		cancel = builder.get_object ("cancel")
		
		self.image = builder.get_object ("image")
		self.entry = builder.get_object ("entry")
		
		submit.connect ("clicked", self.__on_submit)
	
	
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
	

	def load (self, pixbuf):
		'''
		Load the captcha window with the specified pixbuf
		'''
		self.image.set_from_pixbuf (pixbuf)
	
	def __on_submit (self, button):
		pass