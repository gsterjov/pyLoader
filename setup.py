#!/usr/bin/env python

from subprocess import Popen, PIPE
from setuptools import setup, find_packages

from distutils.core import setup
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data


class post_install (_install):
	def run (self):
		_install.run (self)


class install_data (_install_data):
	def run (self):
		_install_data.run (self)
		command = ("glib-compile-schemas", "/usr/share/glib-2.0/schemas/")
		print (" ".join (command))
		Popen (command, stdout=PIPE, stderr=PIPE).communicate()


setup(
	name = "pyloader",
	version = "0.1",
	fullname = "pyLoader",

	author = "Goran Sterjov",
	author_email = "goran.sterjov@gmail.com",
	description = "A GTK+3 GUI for the pyload download manager",
	license = "GPLv3",
	keywords = "pyload download manager gui graphical interface gtk gnome",
	url = "https://github.com/gsterjov/pyLoader",


	packages = find_packages (exclude=["tests.*", "tests"]),

	package_data = {
		"pyloader": ["ui/*.xml"]
	},

	data_files = [
		('/usr/share/glib-2.0/schemas', ['data/org.pyLoader.gschema.xml'])
	],

	entry_points = {
		'console_scripts': ['pyloader = pyloader.window:start']
	},

	install_requires = ['thrift'],
	zip_safe = False,

	cmdclass = {
		"install": post_install,
		"install_data": install_data,
	},
)