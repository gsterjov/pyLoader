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

from event import Event


class remote_property (object):
	'''
	Decorator for raising a specified event whenever the property has changed.
	
	It can be used as following:
	
		import random
		
		class MyClass (object):
			
			def __init__ (self):
				self.my_prop.changed += self.on_my_prop_changed
			
			@live_property
			def my_prop (self):
				return random.randint (0, 100)
			
			def on_my_prop_changed (self, prop, value):
				print "'{0}' Changed: {1}".format (prop, value)
	
	It does this by caching the property value in the _value attribute and
	comparing it with each invocation of the property. Whenever they no longer
	evaluate it will raise the changed event and store the new value into the
	_value attribute
	'''
	
	changed = None
	
	
	def __init__ (self, func):
		self._value = None
		self.changed = Event()
		
		self.func = func
	
	
	def __get__ (self, instance, owner):
		self._instance = instance
		return self
	
	
	def __repr__ (self):
		return self.func.__doc__
	
	
	@property
	def value (self):
		'''
		Get the property value. This is a cached value since the last time the
		property was updated
		'''
		return self._value
	

	def update (self, data=None):
		'''
		Updates the currently cached value.

		If data is None then it will execute the property function to make the
		request for data, otherwise it will pass it the data so it can process it
		and update the cached value if necessary.
		'''
		val = self.func (self._instance, data)
		if data: self.set_value (val)


	def set_value (self, value):
		'''
		Sets the cached property value and raises the changed event if they differ.
		'''
		if value != self._value:
			self._value = value
			self.changed (self.func, value)