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

from twisted.python import log
from twisted.internet import gtk3reactor
gtk3reactor.install()

from gi.repository import Gtk, Gio
from twisted.internet import reactor

from window import MainWindow


def start():
	logging.basicConfig (level=logging.DEBUG, format="%(asctime)s %(levelname)-8s  %(message)s", datefmt="%d/%m/%Y %H:%M:%S")

	observer = log.PythonLoggingObserver()
	observer.start()

	app = Gtk.Application.new ("org.pyLoader", Gio.ApplicationFlags.IS_SERVICE)
	reactor.registerGApplication (app)

	main_window = MainWindow (app)
	reactor.run()