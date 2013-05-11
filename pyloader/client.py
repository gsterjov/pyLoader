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

import logging

from event import Event
from remote_property import remote_property
from live_property import LiveProperty, live_property
from live_dict_property import live_dict_property

# from items import Package, Link, Download
from package import Package

from gi.repository import GLib

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from protocols import PyloadAPIFactory, PyloadEventFactory, PyloadAPIProtocol, PyloadEventProtocol



class ConnectionFailed (Exception):
	pass

class LoginRequired (Exception):
	pass



class PackageQueue (object):
	'''
	A simple package queue that raises events when its modified.
	'''

	def __init__ (self):
		self.queue = {}


	def add (self, item):
		'''
		Add a package to the queue
		'''
		if not self.queue.has_key (item.id):
			self.queue[item.id] = item
		else:
			raise Exception ("Package item already exists")


	def remove (self, pid):
		'''
		Remove a package from the queue
		'''
		if self.queue.has_key (pid):
			item = self.queue[pid]
			del self.queue[pid]
			return item
		else:
			raise KeyError()


	def update (self, pid, item):
		'''
		Update an existing package in the queue
		'''
		if self.queue.has_key (pid):
			self.queue[pid].parse (item)
		else:
			raise KeyError()


	def exists (self, pid):
		'''
		Check to see if the package already exists in the queue
		'''
		return self.queue.has_key (pid)



class Client (object):
	'''
	This class handles all communication to and from the backend pyLoad server
	instance
	
	Events:
		on_connected: Raised when a connection to the backend server is made
		on_disconnected: Raised when the connection has been severed
	'''
	
	on_event = None
	on_connected = None
	on_disconnected = None
	
	
	def __init__ (self):
		'''
		Constructor
		'''
		self.api = None
		self.pub = None

		self.__connected = False
		
		self.on_event = Event()
		self.on_connected = Event()
		self.on_disconnected = Event()

		self.version = LiveProperty ("version")
		self.free_space = LiveProperty ("free_space")
		self.links_queued = LiveProperty ("links_queued")
		self.links_total = LiveProperty ("links_total")

		self.packages = PackageQueue()

		self.tasks = {}
		self.events = []



	def connect (self, host, port, username, password):
		'''
		Connect to the specified backend
		'''
		self.__connected = False
		
		self.host = host
		self.port = port
		self.username = username
		self.password = password


		# API connection
		url = "ws://{0}:{1}/api".format (host, port)

		# create protocol factory
		factory = PyloadAPIFactory (username, password, url)
		factory.protocol = PyloadAPIProtocol

		endpoint = TCP4ClientEndpoint (reactor, host, port)

		d = endpoint.connect (factory)
		d.addCallback (self.on_new_connection)
		# d.addErrback (self.on_error)


		# Publisher connection
		url = "ws://{0}:{1}/async".format (host, port)

		# create protocol factory
		factory = PyloadEventFactory (username, password, url)
		factory.protocol = PyloadEventProtocol

		endpoint = TCP4ClientEndpoint (reactor, host, port)

		d = endpoint.connect (factory)
		d.addCallback (self.on_new_connection)
		# d.addErrback (self.on_error)

		return True


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
	def speed (self):
		'''
		The current download speed in bytes
		'''
		status = self.client.getServerStatus()
		return status['speed']
	
	@property
	def paused (self):
		'''
		Whether or not the queue is currently paused
		'''
		status = self.client.getServerStatus()
		return status['paused']
	
	@property
	def download_enabled (self):
		'''
		Whether or not downloading is enabled
		'''
		status = self.client.getServerStatus()
		return status['download']
	
	@property
	def reconnect_enabled (self):
		'''
		Whether or not the downloader will reconnect when needed
		'''
		status = self.client.getServerStatus()
		return status['reconnect']
	
	

	def get_user_details (self):
		'''
		Get the details of the currently logged in user
		'''
		data = self.client.getUserData (self.username, self.password)
		return {'name': data.name, 'email': data.email, 'role': data.role, 'permission': data.permission}
	
	
	def pause (self):
		'''
		Pause the current queue. This will only stop processing of the queue,
		any links downloading will continue to do so
		'''
		self.api.send ("pauseServer")
	

	def resume (self):
		'''
		Resume the current queue
		'''
		self.api.send ("unpauseServer")
	


	def request_server_status (self):
		'''
		Send a request for server status details.
		The appropriate properties will be updated as a result.
		'''
		self.api.send ("getServerVersion")
		self.api.send ("freeSpace")
		self.api.send ("getServerStatus")


	def request_queue_update (self):
		self.api.send ("getAllFiles")

	
	@live_property
	def queue (self):
		'''
		A dict of packages currently in the queue
		'''
		packages = {}
		
		for item in self.client.getQueueData():
			packages[item.pid] = Package (item)

		return packages
	
	
	@live_property
	def downloads (self):
		'''
		A dict of all active downloads
		'''
		downloads = {}
		
		for item in self.client.statusDownloads():
			downloads[item.fid] = Download (item)

		return downloads


	@live_property
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
		# for prop in self.properties_to_poll:
		# 	prop.update()
		
		# self.collector.update()
		# self.queue.update()
		# self.downloads.update()
		# self.captchas.update()

		# self.poll_tasks()
		
		return True


	def on_api_response (self, response, request):
		'''
		This is the server message receiver from API and publisher connections.
		It will set the appropriate properties based on the request
		attached to the message.
		'''
		if request[0] == "getServerVersion":
			self.version.update (response)

		elif request[0] == "freeSpace":
			self.free_space.update (response)

		elif request[0] == "getServerStatus":
			self.links_queued.update (response['linksqueue'])
			self.links_total.update (response['linkstotal'])

		elif request[0] == "getAllFiles":
			for pid, item in response["packages"].iteritems():
				if self.packages.exists (pid):
					self.packages.update (pid, item)
				else:
					self.packages.add (Package (item))


	def on_publisher_event (self, event):
		print event


	def on_connection_error (self, code, error):
		# handle error responses
		if code == 400: raise result
		elif code == 404: raise AttributeError ("Invalid API Call")
		elif code == 500: raise Exception ("Server Exception: {0}".format(result))
		elif code == 401: raise Unauthorised()
		elif code == 403: raise PermissionDenied()

		logging.warn ("Unknown server error occurred: ({0}) {1}".format(code, error))


	def on_connection_ready (self, protocol):
		'''
		The connection has been opened and is ready to receive messages
		'''
		logging.info ("Logged in to '{0}' as user '{1}'".format(protocol.factory.url, protocol.factory.username))

		if not self.__connected and self.api.ready and self.pub.ready:
			self.__connected = True
			self.on_connected()


	def on_new_connection (self, protocol):
		'''
		A new connection has been made to the pyload server.
		This handles the protocol and makes it available for use to the entire client
		'''
		if protocol.factory.path == "/api":
			self.api = protocol
			protocol.on_response += self.on_api_response
			logging.info ("Connected to API at '{0}'".format (protocol.factory.url))

		elif protocol.factory.path == "/async":
			self.pub = protocol
			protocol.on_event += self.on_publisher_event
			logging.info ("Connected to publisher at '{0}'".format (protocol.factory.url))

		protocol.on_ready += self.on_connection_ready
		protocol.on_error += self.on_connection_error