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

def format_size (bytes):
	'''
	Format the specified size (bytes) into a human readable value
	'''
	abbrevs = (
		(1<<30L, 'GB'),
		(1<<20L, 'MB'),
		(1<<10L, 'kB'),
		(1, 'bytes'),
	)
	
	for factor, suffix in abbrevs:
		if bytes >= factor:
			break
	
	return '{0:.1f} {1}'.format (float(bytes) / float(factor), suffix)


def format_time(self, seconds):
	'''
	Format the specified time (seconds) into a human readable value
	'''
	text = ""
	
	# humanise time value
	min, sec = divmod(seconds, 60)
	hrs, min = divmod(min, 60)
	
	if hrs > 0: text += "{0} hours, ".format(int(hrs))
	if min > 0: text += "{0} minutes, ".format(int(min))
	
	text += "{0} seconds".format(int(sec))
	return text