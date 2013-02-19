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


class CaptchaWindow(object):
	'''
	classdocs
	'''


	def __init__(self):
		'''
		Constructor
		'''
		builder = Gtk.Builder()
		builder.add_from_file ("ui/captcha_notify.xml")
		
		self.window = builder.get_object ("captcha_window")
		submit = builder.get_object ("submit")
		cancel = builder.get_object ("cancel")
		
		self.image = builder.get_object ("image")
		self.entry = builder.get_object ("entry")
		
		submit.connect ("clicked", self.submit)
	
	
	def show (self):
		return self.window.show_all()
	
	def hide (self):
		return self.window.hide()
	

	def load (self, pixbuf):
		'''
		Load the captcha window with the specified pixbuf
		'''
		pass

	
	def submit (self, button):
		pass