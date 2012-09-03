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

from gi.repository import GLib
from module.remote.thriftbackend.ThriftClient import ThriftClient, WrongLogin


from event import Event
from items import Package
from items import Link


class Server(object):
	'''
	classdocs
	'''

	queue_changed = Event() # args: queue, total
	speed_changed = Event() # args: speed
	link_changed = Event() # args: link
	
	package_added = Event() # args: package
	package_removed = Event() # args: package
	
	link_added = Event() # args: link
	
	
	def __init__(self):
		'''
		Constructor
		'''
		self.online_check_id = -1
		self.link_check = {}
		
		self.packages = {}
		
		self.__cache = {'queue': 0, 'total': 0, 'speed': 0, 'links': set()}
	
	
	def _poll_queue (self):
		packages = self.get_queue()
		
		package_ids = set()
		for package in packages:
			package_ids.add (package.id)
		
		# remove packages no longer in the queue
		for id in self.packages.iterkeys():
			if not id in package_ids:
				self.packages.pop (id)
				self.package_removed (id)
		
		# add packages newly added in the queue
		for package in packages:
			if not self.packages.has_key(package.id):
				self.packages[package.id] = package
				self.package_added (package)
	
	
	def poll (self):
		cache = self.__cache
		
		status = self.client.statusServer()
		
		# check queue status
		if status.queue != cache['queue']:
			cache['queue'] = status.queue
			self.queue_changed (status.queue, status.total)
		
		elif status.total != cache['total']:
			self._poll_queue()
			cache['total'] = status.total
			self.queue_changed (status.queue, status.total)
		
		# check speed status
		if status.speed != cache['speed']:
			cache['speed'] = status.speed
			self.speed_changed (status.speed)
		
		
		# check link status
		active_links = set()
		for link in self.client.statusDownloads():
			active_links.add (link.fid)
		
		link_cache = cache['links']
			
		
		for link_id in link_cache:
			if link_id not in active_links:
				self.link_changed(link_id)
		
		for link in active_links:
			# new link active
			if not link in link_cache:
				link_cache.add (link)
				#print link
		
		
		packages = self.client.getQueue()
		for package in packages:
			pass
			#print self.client.getPackageInfo (package.pid)
		
		
		return True
	
	
	def connect (self, host="localhost", port=7227, username=None, password=None):
		# try connecting to the thrift backend
		try:
			self.client = ThriftClient (host, port, username, password)
			self.host = host
			self.port = port
		
		except WrongLogin:
			print "Invalid login"
	
	
	def get_version (self):
		return self.client.getServerVersion()
	
	def get_host (self):
		return self.host
	
	
	def get_free_space(self):
		return self.client.freeSpace()
	
	
	def get_status(self):
		return self.client.statusServer()
	
	
	def get_downloads(self):
		return self.client.statusDownloads()
	
	
	def get_queue(self):
		queue = []
		
		for item in self.client.getQueue():
			queue.append(Package(self.client, item))
		
		return queue
	
	
	def get_captcha(self):
		return self.client.getCaptchaTask(False)
	
	
	def check_online_status(self, links):
		urls = []
		
		# add the link to the dictionary for updates
		for link in links:
			urls.append(link.url)
			self.link_check[link.url] = link
		
		# execute the check
		check = self.client.checkOnlineStatus(urls)
		self.online_check_id = check.rid
	
	
	def check_captcha_waiting(self):
		return self.client.isCaptchaWaiting()
	
	
	def process_pending_jobs(self):
		# poll results for the online check
		if self.online_check_id >= 0:
			results = self.client.pollResults(self.online_check_id)
			
			# update each link with the results
			for url, data in results.data.iteritems():
				link = self.link_check[url]
				link.name = data.name
				link.plugin = data.plugin
				link.status = data.status
				link.size = data.size
			
			# if the returned ID is -1 it means it has finished the check
			self.online_check_id = results.rid
	
	
	def start(self):
		self.client.unpauseServer()
	
	
	def stop(self):
		self.client.pauseServer()
		self.client.stopAllDownloads()
