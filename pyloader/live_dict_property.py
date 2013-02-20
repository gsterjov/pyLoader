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


class live_dict_property (object):
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
	
	added = None
	removed = None
	changed = None
	
	
	def __init__ (self, func):
		self._value = {}
		self.added = Event()
		self.removed = Event()
		self.changed = Event()
		
		self.func = func
	
	
	def __get__ (self, instance, owner):
		self._instance = instance
		return self
	
	
	def __repr__ (self):
		return self.func.__doc__
	
	
	@property
	def dict (self):
		'''
		Get the property value. If the value has changed since last time it
		was accessed it will raise the changed event
		'''
		self.update()
		return self._value
	
	
	def update (self):
		'''
		Updates the currently cached value by executing the property function.
		
		This is called everytime the property is accessed but for those that
		want to force it (such as in a polling loop) they can call this function
		which will act as if it had been accessed
		'''
		val = self.func (self._instance)
		
		# determine if the dict has changed at all
		for key, item in val.iteritems():

			# item cached
			if self._value.has_key (key):
				# item changed
				if self._value[key] != item:
					self._value[key] = item
					self.changed (self._instance, item)

			# new item
			else:
				self._value[key] = item
				self.added (self._instance, item)

		# find out if a cached item has been removed
		for key, item in self._value.items():

			# cached item not in dict
			if not val.has_key (key):
				del self._value[key]
				self.removed (self._instance, item)