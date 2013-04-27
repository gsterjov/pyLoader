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

from remote.websocket_client import WebsocketClient

from event import Event
from live_property import live_property
from live_dict_property import live_dict_property

from items import Package, Link, Download



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
	'''
	
	on_connected = None
	on_disconnected = None
	
	
	def __init__ (self):
		'''
		Constructor
		'''
		self.client = WebsocketClient()
		self.__connected = False
		
		self.on_connected = Event()
		self.on_disconnected = Event()
		
		# set all live properties in this class for polling
		self.properties_to_poll = [
			self.links_active,
			self.links_waiting,
			self.links_total,
			self.speed,
		]

		self.tasks = {}



	def connect (self, host, port, username, password):
		'''
		Connect to the specified backend
		'''
		self.__connected = False
		
		self.host = host
		self.port = port
		self.username = username
		self.password = password

		url = "ws://{0}:{1}/api".format (host, port)
		
		try:
			self.client.open (url)
			logging.info ("Connected to {0}:{1}".format(host, port))
		
		except:
			logging.warn ("Failed to connect to {0}:{1}".format(host, port))
			raise ConnectionFailed
		

		self.client.login (username, password)
		self.__connected = True

		logging.info ("Server version: {0}".format(self.version))
		self.on_connected()

		return True


	@login_required
	def disconnect (self):
		'''
		Disconnect and release the resources from the backend
		'''
		self.backend.close()
		logging.info ("Disconnected from {0}:{1}".format(self.host, self.port))

		self.__connected = False

		self.ws = None
		self.host = None
		self.port = None
		self.username = None
		self.password = None
		
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
		status = self.client.getServerStatus()
		return 0
		# return status['active']
	
	@live_property
	@login_required
	def links_waiting (self):
		'''
		The amount of links currently waiting
		'''
		status = self.client.getServerStatus()
		return status['linksqueue']
	
	@live_property
	@login_required
	def links_total (self):
		'''
		The total amount of links in the queue
		'''
		status = self.client.getServerStatus()
		return status['linkstotal']
	
	@live_property
	@login_required
	def speed (self):
		'''
		The current download speed in bytes
		'''
		status = self.client.getServerStatus()
		return status['speed']
	
	@property
	@login_required
	def paused (self):
		'''
		Whether or not the queue is currently paused
		'''
		status = self.client.getServerStatus()
		return status['paused']
	
	@property
	@login_required
	def download_enabled (self):
		'''
		Whether or not downloading is enabled
		'''
		status = self.client.getServerStatus()
		return status['download']
	
	@property
	@login_required
	def reconnect_enabled (self):
		'''
		Whether or not the downloader will reconnect when needed
		'''
		status = self.client.getServerStatus()
		return status['reconnect']
	
	
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
	
	
	@live_property
	@login_required
	def collector (self):
		'''
		A dict of packages currently in the collector
		'''
		packages = {}
		
		for item in self.client.getCollectorData():
			packages[item.pid] = Package (item)

		return packages
	
	
	@live_property
	@login_required
	def queue (self):
		'''
		A dict of packages currently in the queue
		'''
		packages = {}
		
		for item in self.client.getQueueData():
			packages[item.pid] = Package (item)

		return packages
	
	
	@live_property
	@login_required
	def downloads (self):
		'''
		A dict of all active downloads
		'''
		downloads = {}
		
		for item in self.client.statusDownloads():
			downloads[item.fid] = Download (item)

		return downloads


	@live_property
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


	def restart_link (self, link):
		'''
		Restarts the link so that it can be downloaded again
		'''
		self.client.restartFile (link.id)


	def abort_link (self, link):
		'''
		Aborts the link
		'''
		self.client.stopDownloads ([link.id])


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

		self.tasks[results.rid] = items


	def clear_finished (self):
		'''
		Clears all the finished packages and removes them from the list.
		'''
		ids = self.client.deleteFinished()


	def answer_captcha (self, captcha, answer):
		'''
		Set the answer to a captcha challenge
		'''
		self.client.setCaptchaResult (captcha.tid, answer)



	def poll_tasks (self):
		'''
		Poll the backend for results on a previously queued online check task
		'''
		finished = []

		for rid, links in self.tasks.iteritems():
			results = self.client.pollResults (rid)

			if results.rid == -1:
				finished.append (rid)

				for url, result in results.data.iteritems():
					link = links[url]
					link.name = result.name
					link.size = result.size
					link.plugin = result.plugin
					link.status = Link.Status (result.status)

		for rid in finished:
			del self.tasks[rid]

	
	
	def poll (self):
		'''
		Poll the backend server. This will check all the 'live' properties for
		any changes and raise the property_changed event
		'''
		for prop in self.properties_to_poll:
			prop.update()
		
		self.collector.update()
		self.queue.update()
		self.downloads.update()
		self.captchas.update()

		self.poll_tasks()
		
		return True