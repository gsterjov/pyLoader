#!/usr/bin/env python

from setuptools import setup, find_packages

from distutils.core import setup
from distutils.command.install import install as _install


class post_install (_install):
	def run (self):
		_install.run (self)


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
	package_data = {"pyloader": ["ui/*.xml"]},
	zip_safe = False,

	entry_points = {
		'console_scripts': ['pyloader = pyloader.window:start']
	},

	install_requires = ['thrift'],

	cmdclass = {"install": post_install},
)