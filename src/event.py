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

class Event (object):
	'''
	classdocs
	'''


	def __init__ (self):
		'''
		Constructor
		'''
		self.handlers = set()
	
	
	def attach (self, handler):
		self.handlers.add (handler)
		return self
	
	
	def detach (self, handler):
		try:
			self.handlers.remove (handler)
		except:
			pass
		
		return self
	
	
	def fire (self, *args, **kargs):
		for func in self.handlers:
			func (*args, **kargs)
	
	
	__iadd__ = attach
	__isub__ = detach
	__call__  = fire
