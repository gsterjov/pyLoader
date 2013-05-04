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

import json
import logging

from event import Event
from live_property import live_property
from live_dict_property import live_dict_property

from items import Package, Link, Download

from gi.repository import GLib

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol



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



class PyloadClientFactory (WebSocketClientFactory):

	def __init__ (self, username, password, *args, **kwargs):
		self.username = username
		self.password = password

		WebSocketClientFactory.__init__ (self, *args, **kwargs)


class PyloadClientProtocol (WebSocketClientProtocol):

	on_error = None
	on_ready = None
	on_message = None


	def __init__ (self):
		self.ready = False
		self.on_error = Event()
		self.on_ready = Event()
		self.on_message = Event()


	def onMessage (self, msg, binary):
		code, result = json.loads (msg)

		if not code == 200:
			on_error (code, result)
		
		else:
			# assume we are trying to log in
			if not self.ready:
				self.ready = True
				self.on_ready (self)
			else:
				self.on_message (msg)


	def onOpen (self):
		auth = [self.factory.username, self.factory.password]
		request = json.dumps (["login", auth])
		self.sendMessage (request)


	def send (self, method, *args, **kwargs):
		'''
		Send a request to the pyload API. This will be sent
		in the form of a JSON object with the method name and arguments
		supplied.

		param method The name of the API method to call
		param *args Any arugments to pass to the API method
		'''
		if not self.ready: return

		request = json.dumps ([method, args])

		logging.debug ("Sending request to '{0}': {1}".format(self.factory.url, request))
		self.sendMessage (request)



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
		self.api = None
		self.pub = None

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
		self.events = []


	def on_connection_message (self, message):
		print message


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
			logging.info ("Connected to API at '{0}'".format (protocol.factory.url))
			self.api = protocol

		elif protocol.factory.path == "/async":
			logging.info ("Connected to publisher at '{0}'".format (protocol.factory.url))
			self.pub = protocol

		protocol.on_ready += self.on_connection_ready
		protocol.on_message += self.on_connection_message



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
		factory = PyloadClientFactory (username, password, url)
		factory.protocol = PyloadClientProtocol

		endpoint = TCP4ClientEndpoint (reactor, host, port)

		d = endpoint.connect (factory)
		d.addCallback (self.on_new_connection)
		# d.addErrback (self.on_error)


		# Publisher connection
		url = "ws://{0}:{1}/async".format (host, port)

		# create protocol factory
		factory = PyloadClientFactory (username, password, url)
		factory.protocol = PyloadClientProtocol

		endpoint = TCP4ClientEndpoint (reactor, host, port)

		d = endpoint.connect (factory)
		d.addCallback (self.on_new_connection)
		# d.addErrback (self.on_error)

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
		self.api.send ("getServerVersion")
		return 0
		# return self.client.getServerVersion()
	
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
		# for prop in self.properties_to_poll:
		# 	prop.update()
		
		# self.collector.update()
		# self.queue.update()
		# self.downloads.update()
		# self.captchas.update()

		# self.poll_tasks()
		
		return True