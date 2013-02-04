#
#    Copyright 2012 Goran Sterjov
#    This file is part of pyLoader.
#
#    pyLoader is free software: you can redistribute it and/or modify
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
#    along with pyLoader.  If not, see <http://www.gnu.org/licenses/>.
#

import logging

from pyload import Pyload

from thrift.transport.TSocket import TSocket
from thrift.transport.TTransport import TBufferedTransport
from thrift.protocol.TBinaryProtocol import TBinaryProtocol

from event import Event
from live_property import live_property
from live_dict_property import live_dict_property

from items import Package, Link, ActiveLink



class ConnectionFailed (Exception):
	pass

class LoginRequired (Exception):
	pass



class login_required (object):
	'''
	Decorator which ensures that the client is currently logged into the backend
	server, otherwise raise a LoginRequired exception
	'''
	def __init__ (self, func):
		self.func = func
	
	def __call__ (self, instance, *args, **kwargs):
		if instance.connected:
			return self.func (instance, *args, **kwargs)
		
		raise LoginRequired
	
	def __repr__ (self):
		return self.func.__doc__
	


class Client (object):
	'''
	This class handles all communication to and from the backend pyLoad server
	instance
	
	Events:
		on_connected: Raised when a connection to the backend server is made
		on_disconnected: Raised when the connection has been severed
		on_queue_added: Raised when a package has been added to the queue
		on_package_added: Raised when a package has been added to the collector

		on_link_status: Raised when an online check status has changed for a link
	'''
	
	on_connected = None
	on_disconnected = None

	on_queue_added = None
	on_queue_removed = None
	on_active_added = None
	on_active_removed = None
	on_collector_added = None
	on_collector_removed = None
	on_finished_added = None

	on_active_changed = None
	on_link_checked = None
	
	
	def __init__ (self):
		'''
		Constructor
		'''
		self.__connected = False
		
		self.on_connected = Event()
		self.on_disconnected = Event()

		self.on_queue_added = Event()
		self.on_queue_removed = Event()
		self.on_active_added = Event()
		self.on_active_removed = Event()
		self.on_collector_added = Event()
		self.on_collector_removed = Event()
		self.on_finished_added = Event()

		self.on_active_changed = Event()
		self.on_link_checked = Event()
		
		# set all live properties in this class for polling
		self.properties_to_poll = [
			self.links_active,
			self.links_waiting,
			self.links_total,
			self.speed,
		]
		
		self._queue_cache = {}
		self._active_cache = {}
		self._collector_cache = {}
		self._finished_cache = {}
		self._online_check_cache = {}


	def connect (self, host, port, username, password):
		'''
		Connect to the specified backend
		'''
		self.__connected = False
		
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		
		self.socket = TSocket (host, port)
		self.transport = TBufferedTransport (self.socket)
		self.protocol = TBinaryProtocol (self.transport)
		self.client = Pyload.Client (self.protocol)
		
		try:
			self.transport.open()
			self.__connected = True
			logging.info ("Connected to {0}:{1}".format(host, port))
		
		except:
			logging.warn ("Failed to connect to {0}:{1}".format(host, port))
			raise ConnectionFailed
		
		if self.client.login (username, password):
			logging.info ("Server version: {0}".format(self.version))
			self.on_connected()
			return True
		
		return False
		

	@login_required
	def disconnect (self):
		'''
		Disconnect and release the resources from the backend
		'''
		self.transport.close()
		self.__connected = False
		
		self.client = None
		self.protocol = None
		self.transport = None
		self.socket = None
		
		self.host = None
		self.port = None
		self.username = None
		self.password = None
		
		logging.info ("Disconnected from {0}:{1}".format(self.host, self.port))
		self.on_disconnected()
	
	
	@property
	def connected (self):
		'''
		Whether or not the client is connected to a server
		'''
		return self.__connected
		
	
	@property
	@login_required
	def version (self):
		'''
		Get the version of the server
		'''
		return self.client.getServerVersion()
	
	@property
	@login_required
	def free_space (self):
		'''
		The amount of free space in the download directory
		'''
		return self.client.freeSpace()
	
	@live_property
	@login_required
	def links_active (self):
		'''
		The amount of links currently active
		'''
		status = self.client.statusServer()
		return status.active
	
	@live_property
	@login_required
	def links_waiting (self):
		'''
		The amount of links currently waiting
		'''
		status = self.client.statusServer()
		return status.queue
	
	@live_property
	@login_required
	def links_total (self):
		'''
		The total amount of links in the queue
		'''
		status = self.client.statusServer()
		return status.total
	
	@live_property
	@login_required
	def speed (self):
		'''
		The current download speed in bytes
		'''
		status = self.client.statusServer()
		return status.speed
	
	@property
	@login_required
	def paused (self):
		'''
		Whether or not the queue is currently paused
		'''
		status = self.client.statusServer()
		return status.pause
	
	@property
	@login_required
	def download_enabled (self):
		'''
		Whether or not downloading is enabled
		'''
		status = self.client.statusServer()
		return status.download
	
	@property
	@login_required
	def reconnect_enabled (self):
		'''
		Whether or not the downloader will reconnect when needed
		'''
		status = self.client.statusServer()
		return status.reconnect
	
	
	@login_required
	def get_user_details (self):
		'''
		Get the details of the currently logged in user
		'''
		data = self.client.getUserData (self.username, self.password)
		return {'name': data.name, 'email': data.email, 'role': data.role, 'permission': data.permission}
	
	
	@login_required
	def pause (self):
		'''
		Pause the current queue. This will only stop processing of the queue,
		any links downloading will continue to do so
		'''
		self.client.pauseServer()
	
	@login_required
	def resume (self):
		'''
		Resume the current queue
		'''
		self.client.unpauseServer()
	
	
	@live_dict_property
	@login_required
	def queue (self):
		'''
		A dict of packages currently in the queue
		'''
		packages = {}
		
		for item in self.client.getQueue():
			packages[item.pid] = Package (self.client, item)

		return packages

	@live_dict_property
	@login_required
	def captchas (self):
		'''
		The current captcha tasks waiting to be actioned
		'''
		captchas = {}

		if self.client.isCaptchaWaiting():
			task = self.client.getCaptchaTask (False)
			captchas[task.tid] = task

		return captchas


	def queue_package (self, package):
		'''
		Adds the specified package to the queue
		'''
		self.client.pushToQueue (package.id)


	def check_online_status (self, links):
		'''
		Queues a task to check the online status of the specified link items.
		The results will automatically be set on the link item
		'''
		# add the link to the results data cache
		items = {}
		for link in links:
			items[link.url] = link

		# send the check request
		urls = items.keys()
		results = self.client.checkOnlineStatus (urls)

		# update the first results
		self._online_check_cache[results.rid] = items
		self._update_online_check_cache (results.rid, results)

	
	
	def poll_queue (self):
		'''
		Poll the backend queue for new packages or changes to existing ones
		'''
		queue = self.client.getQueue()
		ids = []
		
		for item in queue:
			ids.append (item.pid)

			# update package
			if self._queue_cache.has_key (item.pid):
				pass
			
			# add package
			else:
				package = Package (self.client, item)
				self._queue_cache[item.pid] = package
				self.on_queue_added (package)
		

		# remove packages from the cache
		for package_id, package in self._queue_cache.items():
			if not package_id in ids:
				self.on_queue_removed (package)
				del self._queue_cache[package_id]
		
		return True


	def poll_active (self):
		'''
		Poll the backed for the status of all active downloads
		'''
		active = self.client.statusDownloads()

		for item in active:
			# update link
			if self._active_cache.has_key (item.fid):
				self._update_active_cache (item)
				self.on_active_changed()

			# add link
			else:
				link = ActiveLink()
				self._active_cache[item.fid] = link
				self._update_active_cache (item)
				self.on_active_added (link)

		return True


	def poll_collector (self):
		'''
		Poll the backend collector for new packages or changes to existing ones
		'''
		collector = self.client.getCollector()
		ids = []
		
		# add packages to the cache
		for item in collector:
			ids.append (item.pid)

			# update package
			if self._collector_cache.has_key (item.pid):
				pass

			elif self._finished_cache.has_key (item.pid):
				pass
			
			# add package
			else:
				package = Package (self.client, item)

				# pyload puts finished packages back into the collector for some reason
				if package.finished:
					self._finished_cache[item.pid] = package
					self.on_finished_added (package)

				else:
					self._collector_cache[item.pid] = package
					self.on_collector_added (package)
		

		# remove packages from the cache
		for package_id, package in self._collector_cache.items():
			if not package_id in ids:
				self.on_collector_removed (package)
				del self._collector_cache[package_id]

		return True


	def poll_online_checks (self):
		'''
		Poll the backend for results on a previously queue online check task
		'''
		for rid, data in self._online_check_cache.items():
			results = self.client.pollResults (rid)
			self._update_online_check_cache (rid, results)


	def poll_captcha (self):
		'''
		Poll for captcha tasks waiting to be actioned in the backend
		'''
		if self.client.isCaptchaWaiting():
			print self.client.getCaptchaTask()
	
	
	def poll (self):
		'''
		Poll the backend server. This will check all the 'live' properties for
		any changes and raise the property_changed event
		'''
		for prop in self.properties_to_poll:
			prop.update()
		
		self.queue.update()
		self.captchas.update()

		# self.poll_queue()
		# self.poll_active()
		# self.poll_collector()
		# self.poll_online_checks()
		
		return True



	def _update_active_cache (self, status):
		'''
		Helper method to process the active download status and update
		the associated items and cache
		'''
		link = self._active_cache[status.fid]

		link.id = status.fid
		link.size = status.size
		link.speed = status.speed
		link.bytes_left = status.bleft
		link.eta = status.eta
		link.wait_time = status.wait_until
		link.percent = status.percent


	def _update_online_check_cache (self, rid, results):
		'''
		Helper method to process the online check results and update
		the associated items and cache
		'''
		links = self._online_check_cache[rid]
		
		for url, result in results.data.iteritems():
			link = links[url]

			link.size = result.size
			link.name = result.name
			link.plugin = result.plugin
			link.status = Link.Status (result.status)

		self.on_link_checked ()

		if results.rid == -1:
			del self._online_check_cache[rid]