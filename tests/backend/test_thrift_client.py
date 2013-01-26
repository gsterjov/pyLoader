import unittest
from mock import patch

from backend.thrift_client import Client
from backend.pyload.ttypes import UserData


class TestThriftClient (unittest.TestCase):
	'''
	classdocs
	'''
	
	@patch('backend.thrift_client.Pyload.Client', autospec=True)
	@patch('backend.thrift_client.TBufferedTransport', autospec=True)
	@patch('backend.thrift_client.TSocket', autospec=True)
	def test_connect (self, MockSocket, MockTransport, MockClient):
		'''
		Should connect with the appropriate settings
		'''
		transport_mock = MockTransport.return_value
		transport_mock.open.return_value = True
		
		client_mock = MockClient.return_value
		client_mock.login.return_value = True
		
		client = Client()
		assert client.connect ('test', 1234, 'user', 'pass')
		
		MockSocket.assert_called_with ('test', 1234)
		client_mock.login.assert_called_with ('user', 'pass')
		assert transport_mock.open.called
	
	
	@patch('backend.thrift_client.Pyload.Client', autospec=True)
	@patch('backend.thrift_client.TBufferedTransport', autospec=True)
	def test_disconnect (self, MockTransport, MockClient):
		'''
		Should disconnect and free resources associated with the backend
		'''
		transport_mock = MockTransport.return_value
		
		client = Client()
		client.connect ('test', 1234, 'user', 'pass')
		
		client.disconnect()
		assert transport_mock.close.called
	
	
	@patch('backend.thrift_client.Pyload.Client', autospec=True)
	@patch('backend.thrift_client.TBufferedTransport', autospec=True)
	def test_get_user_details (self, MockTransport, MockClient):
		'''
		Should get the currently logged in user's details
		'''
		client_mock = MockClient.return_value
		client_mock.getUserData.return_value = UserData('test', 'test@test.com', 1, 2)
		
		client = Client()
		client.connect ('test', 1234, 'user', 'pass')
		
		details = client.get_user_details()
		self.assertEqual (details, {'name': 'test', 'email': 'test@test.com', 'role': 1, 'permission': 2})
