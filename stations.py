#!/usr/bin/python3

import sys,os

import xml.dom
from xml.etree.ElementTree import Element, ElementTree, fromstring
# from xmlvalidator import validate_dtd

import logging
import logging.handlers

# setup environment variable defaults
PARADIUM_HOME     = '/opt/paradium/'
PARADIUM_VHOME    = '/var/paradium/'
PARADIUM_MPDHOST  = '127.0.0.1'

# and override with the actual environment
if 'PARADIUM_HOME' in os.environ:
	PARADIUM_HOME = os.environ['PARADIUM_HOME']
if 'PARADIUM_MPDHOST' in os.environ:
	PARADIUM_MPDHOST = os.environ['PARADIUM_MPDHOST']


class Station():
	"""
	represents one radio station
	"""

	def __init__(self, elem):
		"""
		create a Station out of a 'station' typed XML element
		"""
		self.id = int(elem.get('id'))
		self.urls = []

		for child in list(elem):
			if child.tag == 'name':
				self.name = child.text
			elif child.tag == 'website':
				self.website = child.text
			elif child.tag == 'url':
				self.urls.append(child.text)
		return

	def __str__(self):
		retstr = '{} ({})'.format(self.name, self.website)
		assert isinstance(retstr, str)
		return retstr


class Stations():
	"""
	contains all paradium stations as broadcasted by stations.xml

	I treat them as a list, implying that they are ordered
	by nothing but the way they happen to be in the XML.
	"""

	stations = []

	def __init__(self, logger):
		
		try:
			# better kepe the logger for Ron
			self.logger = logger
			
			# read and parse our stations.xml file in which 
			# all the available radio stations are stored
			self.logger.info('parsing stations.xml')
			xmlfile = open(PARADIUM_HOME + '/htdocs/stations.xml', 'r')
			# validate_dtd(xmlfile)
			xml = xmlfile.read()
			xmlfile.close()

			# get the DOM	
			dom = fromstring(xml)

			# and traverse all stations in the root node
			i = dom.iter('station')
			for s in i:
				new_station = Station(s)
				logger.info('inserting station {}'.format(new_station.name))
				self.stations.append(Station(s))
				new_station
		
			print('Stations created')

		except IOError:
			self.logger.error('couldn\'t read stations.xml')

		return

	def get_station(self, id):
		"""
		find a station by id
		:type id = int
		"""
		for s in self.stations:
			if isinstance(id, str):
				if s.id == int(id):
					return s
			elif s.id == id:
				return s
		return None

	def get_next(self, id):
		"""
		get the next station in our list in order to switch to it.
		If we are already at the beginning of the list we switch to the last

		:param id = the station to start from (current)
		"""

		# first find the current station
		for i, val in enumerate(self.stations, 0):
			if val.id == id:
				if i == len(self.stations) - 1:
					return self.stations[0]
				else:
					return self.stations[i + 1]

		# If for some reason things go south I default back to the first station
		return self.stations[0]

	def get_prev(self, id):
		"""
		get the previous station in our list in order to switch to it.
		If we are already at the beginning of the list we switch to the last

		:param id = the station to start from (current)
		"""

		# first find the current station
		for i, val in enumerate(self.stations, 0):
			if val.id == id:
				if i == 0:
					return self.stations[len(self.stations) - 1]
				else:
					return self.stations[i - 1]

		# If for some reason things go south I default back to the first station
		return self.stations[0]

if __name__ == '__main__':

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	filehandler = logging.handlers.TimedRotatingFileHandler('./paradium.log', when='midnight', interval=1, backupCount=10)
	filehandler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
	logger.addHandler(filehandler)

	stations = Stations(logger)



