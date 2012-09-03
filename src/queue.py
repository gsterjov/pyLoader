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

import datetime
from time import time
from gi.repository import Gtk, Gdk
from module.remote.thriftbackend import ThriftClient

from items import Item, Link


class Queue(object):
	'''
	classdocs
	'''

	class Columns:
		(ITEM,
		SPEED,
		ETA,
		BYTES_LEFT,
		WAIT_UNTIL) = range(5)


	def __init__(self, builder, server):
		'''
		Constructor
		'''
		self.queue_tree = builder.get_object("queue_tree")
		
		link = builder.get_object("link")
		host = builder.get_object("host")
		
		self.store = Gtk.TreeStore(Item.__gtype__, int, int, int, int)
		self.queue_tree.set_model(self.store)
		
		area = link.get_area()
		area.set_orientation(Gtk.Orientation.VERTICAL)
		
		name_renderer = Gtk.CellRendererText()
		status_renderer = Gtk.CellRendererText()
		progress_renderer = Gtk.CellRendererProgress()
		host_renderer = Gtk.CellRendererText()
		
		link.pack_start(name_renderer, True)
		link.pack_start(progress_renderer, True)
		link.pack_start(status_renderer, True)
		host.pack_start(host_renderer, True)
		
		link.set_cell_data_func(name_renderer, self.__render_name)
		link.set_cell_data_func(progress_renderer, self.__render_progress)
		link.set_cell_data_func(status_renderer, self.__render_status)
		host.set_cell_data_func(host_renderer, self.__render_host)
		
		
		# get colours
		path = Gtk.WidgetPath()
		path.append_type(Gtk.WindowType)
		
		self.package_ctx = Gtk.StyleContext()
		self.package_ctx.set_path(path)
		self.package_ctx.add_class(Gtk.STYLE_CLASS_INFO)
	
	
	def format_bytes(self, bytes):
		abbrevs = (
			(1<<30L, 'GB'),
			(1<<20L, 'MB'),
			(1<<10L, 'kB'),
			(1, 'bytes'),
		)
		
		for factor, suffix in abbrevs:
			if bytes >= factor:
				break
		
		return '{0:.1f} {1}'.format(float(bytes) / float(factor), suffix)
	
	
	def format_time(self, seconds):
		text = ""
		
		# humanise time value
		min, sec = divmod(seconds, 60)
		hrs, min = divmod(min, 60)
		
		if hrs > 0: text += "{0} hours, ".format(int(hrs))
		if min > 0: text += "{0} minutes, ".format(int(min))
		
		text += "{0} seconds".format(int(sec))
		return text
	
	
	def __set_cell_background(self, cell, item):
		cell.set_property("cell-background-set", False)
		
		if item.is_package:
			if item.links_done == item.links_total:
				cell.set_property("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.4))
			else:
				cell.set_property("cell-background-rgba", Gdk.RGBA(1, 0.7, 0, 0.4))
			
			cell.set_property("cell-background-set", True)
		
		if item.is_link:
			if item.status == Link.Status.FINISHED:
				cell.set_property("cell-background-rgba", Gdk.RGBA(0.5, 1, 0.2, 0.3))
				cell.set_property("cell-background-set", True)
			
			elif item.status in [Link.Status.ABORTED, Link.Status.FAILED, Link.Status.OFFLINE, Link.Status.TEMP_OFFLINE]:
				cell.set_property("cell-background-rgba", Gdk.RGBA(1, 0.2, 0, 0.3))
				cell.set_property("cell-background-set", True)
			
			elif item.status in [Link.Status.WAITING]:
				cell.set_property("cell-background-rgba", Gdk.RGBA(1, 1, 0, 0.5))
				cell.set_property("cell-background-set", True)
	
	
	def __render_name(self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Queue.Columns.ITEM]
		
		# render as a package
		if item.is_package:
			cell.set_property("markup", "<b>{0}</b>".format(item.name))
			#text = "<small>{0}/{1}</small>".format(item.links_done, item.links_total)
		
		# render as a link
		elif item.is_link:
			# get the link size and assume no bytes have been transfered
			size = self.format_bytes(item.size)
			details = "[{0}]".format(size)
			
			# item is downloading so get current bytes transferred
			if item.status == Link.Status.DOWNLOADING:
				bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
				seconds_left = model[iter][Queue.Columns.ETA]
				
				transfered = self.format_bytes(item.size - bytes_left)
				eta = self.format_time(seconds_left)
				details = "[{0} of {1}]  -  {2}".format(transfered, size, eta)
			
			# render link details as markup and make it visible
			text = "{0}<small>  -  {1}</small>".format(item.name, details)
			cell.set_property("markup", text)
			cell.set_property("visible", True)
		
		self.__set_cell_background(cell, item)
	
	
	def __render_status(self, column, cell, model, iter, data):
		# get the item we are dealing with
		item = model[iter][Queue.Columns.ITEM]
		
		# set it to invisible so it doesnt render for packages
		cell.set_property("visible", False)
		
		if item.is_link:
			# get the state of the link
			status = ThriftClient.DownloadStatus._VALUES_TO_NAMES[item.status]
			text = "<b>{0}</b>".format(status)
			
			if item.status == Link.Status.DOWNLOADING:
				# get the current speed and format it
				speed = model[iter][Queue.Columns.SPEED]
				speed = self.format_bytes(speed)
				
				# get current percentage done
				bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
				transferred = item.size - bytes_left
				percent = (float(transferred) / float(item.size)) * 100
				
				text += "  ({0}%)  -  {1}/s".format(int(percent), speed)
			
			elif item.status == Link.Status.WAITING:
				# get the current wait time
				seconds = model[iter][Queue.Columns.WAIT_UNTIL]
				wait_time = self.format_time(seconds - time())
				
				text += "  -  {0} left".format(wait_time)
			
			elif item.status == Link.Status.FAILED:
				text += "  -  {0}".format(item.error)
			
			# render the status and make it visible
			cell.set_property("markup", "<small>{0}</small>".format(text))
			cell.set_property("visible", True)
			
		self.__set_cell_background(cell, item)
	
	
	def __render_progress(self, column, cell, model, iter, data):
		item = model[iter][Queue.Columns.ITEM]
		
		cell.set_property("visible", False)
		
		if item.is_link and item.status == Link.Status.DOWNLOADING:
			bytes_left = self.store[iter][Queue.Columns.BYTES_LEFT]
			bytes_transferred = item.size - bytes_left
			percent = (float(bytes_transferred) / float(item.size)) * 100
			
			cell.set_property("height", 10)
			cell.set_property("text", "")
			cell.set_property("value", percent)
			cell.set_property("visible", True)
	
	
	def __render_host(self, column, cell, model, iter, data):
		item = model[iter][Queue.Columns.ITEM]
		
		if item.is_package:
			cell.set_property("markup", "<small>{0}/{1} completed</small>".format(item.links_done, item.links_total))
		
		elif item.is_link:
			cell.set_property("markup", "<small>{0}</small>".format(item.plugin))
		
		self.__set_cell_background(cell, item)
	
	
	
	def __get_link_iter(self, link_id):
		# get root iterator
		package_iter = self.store.get_iter_first()
		
		# get all packages
		while package_iter != None:
			
			# get all links in the package
			link_iter = self.store.iter_children(package_iter)
			
			while link_iter != None:
				
				# return the link iterator if it matches the ID
				link = self.store[link_iter][Queue.Columns.ITEM]
				if link.id == link_id:
					return link_iter
				
				# get the next link in the list
				link_iter = self.store.iter_next(link_iter)
			
			# get the next package in the list
			package_iter = self.store.iter_next(package_iter)
		
		# the link ID wasnt found
		return None
	
	
	def update_status(self, server):
		downloads = server.get_downloads()
		
		for download in downloads:
			#print download
			link_iter = self.__get_link_iter(download.fid)
			
			self.store.set_value(link_iter, Queue.Columns.SPEED, download.speed)
			self.store.set_value(link_iter, Queue.Columns.ETA, download.eta)
			self.store.set_value(link_iter, Queue.Columns.BYTES_LEFT, download.bleft)
			self.store.set_value(link_iter, Queue.Columns.WAIT_UNTIL, download.wait_until)
	
	
	def check_all_online(self, server):
		'''
		Check all links in the queue for their current online state
		'''
		links = []
		package_iter = self.store.get_iter_first()
		
		# get all packages
		while package_iter != None:
			# get all links in the package
			link_iter = self.store.iter_children(package_iter)
			
			while link_iter != None:
				item = self.store[link_iter][Queue.Columns.ITEM]
				
				# ignore links that are in a status assumed to be online
				if item.status not in [Link.Status.DOWNLOADING, Link.Status.FINISHED, Link.Status.WAITING]:
					links.append(item)
				
				# go to the next link in the package
				link_iter = self.store.iter_next(link_iter)
			
			# go to the next package in the queue
			package_iter = self.store.iter_next(package_iter)
		
		# add the links to the server online check job
		server.check_online_status(links)
	
	
	def add_package (self, package):
		parent = self.store.append (None, [package, 0, 0, 0, 0])
		
		for link in package.links:
			self.store.append (parent, [link, 0, 0, 0, 0])
	
	
	def load_queue(self, server):
		for package in server.get_queue():
			parent = self.store.append(None, [package, 0, 0, 0, 0])
			
			for link in package.links:
				self.store.append(parent, [link, 0, 0, 0, 0])
