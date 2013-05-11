import json
import logging

from collections import deque
from event import Event

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from autobahn.websocket import WebSocketClientFactory, WebSocketClientProtocol



class PyloadBaseFactory (WebSocketClientFactory):

	def __init__ (self, username, password, *args, **kwargs):
		self.username = username
		self.password = password

		WebSocketClientFactory.__init__ (self, *args, **kwargs)


class PyloadAPIFactory (PyloadBaseFactory):
	pass


class PyloadEventFactory (PyloadBaseFactory):

	def __init__ (self, username, password, *args, **kwargs):
		if kwargs.has_key ("interval"):
			self.interval = kwargs["interval"]
			kwargs.pop ("interval")
		else:
			self.interval = 500

		PyloadBaseFactory.__init__ (self, username, password, *args, **kwargs)



class PyloadBaseProtocol (WebSocketClientProtocol):

	on_error = None
	on_ready = None


	def __init__ (self):
		self.ready = False
		self.on_error = Event()
		self.on_ready = Event()


	def on_open (self):
		pass

	def on_message (self, msg):
		pass


	def onMessage (self, msg, binary):
		# haven't logged in yet
		if not self.ready:
			code, result = json.loads (msg)

			# logged in. setup the event loop
			if code == 200:
				self.ready = True
				self.on_open()
				self.on_ready (self)

			else:
				on_error (code, result)

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
		if not self.ready: return None

		request = json.dumps ([method, args])
		logging.debug ("Sending request to '{0}': {1}".format(self.factory.url, request))
		self.sendMessage (request)

		return request




class PyloadAPIProtocol (PyloadBaseProtocol):

	def __init__ (self):
		PyloadBaseProtocol.__init__ (self)
		self.requests = deque([])
		self.on_response = Event()


	def on_message (self, msg):
		request = self.requests.popleft()
		code, result = json.loads (msg)

		if code == 200:
			self.on_response (json.loads(msg)[1], json.loads(request))
		else:
			on_error (code, result)


	def send (self, method, *args, **kwargs):
		request = PyloadBaseProtocol.send (self, method, *args, **kwargs)
		if request:
			self.requests.append (request)




class PyloadEventProtocol (PyloadBaseProtocol):

	def __init__ (self):
		PyloadBaseProtocol.__init__ (self)
		self.on_event = Event()


	def on_open (self):
		# kick off the publisher events
		self.send ("setInterval", 500)
		self.send ("start")


	def on_message (self, msg):
		self.on_event (json.loads (msg))