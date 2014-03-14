#!/usr/bin/python3

import sys,os

import xml.dom
#import easy to use xml parser called minidom:
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, fromstring

import logging
import logging.handlers


class Station():
	"""
	represents one radio station
	"""
	
	name = ''
	urls = []
	website = ''
	current = True

	def __init__(self, elem):

		current = elem.find("name")
		if current is not None:
			self.name = current.text

		current = elem.find("url")
		for url in current:
			self.urls.append(url.text)
	
		current = elem.find("website")
		if current is not None:
			self.website = current.text

		return

	def __str__(self):
		str = '{} ({})'.format(self.name, self.website)
		return str


class Stations():
	"""
	contains all paradium stations as broadcasted by stations.xml
	"""

	stations = []

	def __init__(self, logger):
		
		try:
			# read and parse our stations.xml file in which 
			# all the available radio stations are stored
			logger.info('parsing stations.xml')
			xmlfile = open('/opt/paradium/htdocs/stations.xml', 'r')
			xml = xmlfile.read()
			xmlfile.close()

			# get the DOM
			dom = fromstring(xml)

			# and traverse all stations in the root node
			for s in dom:
				new_station = Station(s)
				logger.info('inserting station {}'.format(new_station.name))
				self.stations.append(new_station)
				print(new_station)

		except IOError:
			logger.error('couldn\'t read stations.xml')

		return


if __name__ == '__main__':

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	filehandler = logging.handlers.TimedRotatingFileHandler('./paradium.log', when='midnight', interval=1, backupCount=10)
	filehandler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
	logger.addHandler(filehandler)

	stations = Stations(logger)



