import json
from websocket import create_connection


class Unauthorised (Exception):
	pass

class PermissionDenied (Exception):
	pass


class WebsocketClient (object):
	'''
	The websocket client that will carry across requests and responses
	from/to the client and pyload server.
	'''

	def __init__ (self):
		self.url = None
		self.socket = None


	def open (self, url):
		self.url = url
		self.socket = create_connection (url)


	def close (self):
		self.socket.close()

		self.socket = None
		self.url = None


	def send (self, method, *args, **kwargs):
		'''
		Send a request to the pyload API. This will be sent
		in the form of a JSON object with the method name and arguments
		supplied.

		param method The name of the API method to call
		param *args Any arugments to pass to the API method
		'''
		request = json.dumps ([method, args])

		self.socket.send (request)
		response = self.socket.recv()

		code, result = json.loads (response)

		# handle error responses
		if code == 400: raise result
		elif code == 404: raise AttributeError ("Invalid API Call: {0}".format(request))
		elif code == 500: raise Exception ("Server Exception: {0}".format(result))
		elif code == 401: raise Unauthorised()
		elif code == 403: raise PermissionDenied()

		return result


	def __getattr__ (self, name):
		'''
		Allows API methods to be called as if they were members of this class
		by sending the request to the server transparently
		'''
		def func (*args, **kwargs):
			return self.send (name, *args, **kwargs)

		return func