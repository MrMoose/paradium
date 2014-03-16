#!/usr/bin/python3

from xml.etree.ElementTree import Element, SubElement, ElementTree, ParseError
import os
import logging
import logging.handlers

# setup environment variable defaults
PARADIUM_HOME     = '/opt/paradium/'
PARADIUM_VHOME    = '/var/paradium/'
PARADIUM_MPDHOST  = '127.0.0.1'

# and override with the actual environment
if 'PARADIUM_HOME' in os.environ:
	PARADIUM_HOME = os.environ['PARADIUM_HOME']
if 'PARADIUM_VHOME' in os.environ:
	PARADIUM_VHOME = os.environ['PARADIUM_VHOME']
if 'PARADIUM_MPDHOST' in os.environ:
	PARADIUM_MPDHOST = os.environ['PARADIUM_MPDHOST']

class DataModel():
	"""
	Dynamic data model for Paradium
	"""
	
	m_current_station = 1
	
	def set_defaults(self):
		"""
		set all data members to default in 
		case we couldn't read/parse/use our data
		"""
		print('setting defaults')
		self.dom = ElementTree()
		root = Element('paradium')
		se = SubElement(root, 'current_station')
		se.text = str(self.m_current_station)
		self.dom._setroot(root)
		
	def __init__(self, logger):
		
		"""

		:type self: object
		"""
		try:
			logger.info('parsing data.xml')
			# get the DOM	
			self.dom = ElementTree()
			self.dom.parse(PARADIUM_VHOME + 'data.xml')

			root = self.dom.getroot()
			if root is None:
				self.set_defaults()
				return

			# and traverse all stations in the root node
			cs = self.dom.getroot().find('current_station')
			if cs is not None:
				self.m_current_station = int(cs.text)

			print ('current station: {}'.format(self.m_current_station))
			return
			
		except IOError:
			logger.warning('couldn\'t read data.xml. Using default values.')
			self.set_defaults()
			return
		
		except ParseError:
			logger.warning('couldn\'t parse data.xml. Using default values.')
			self.set_defaults()
			return

	def set_current_station(self, current_id):
		"""
		set the current station by id
		:type self: int
		"""
		if isinstance(current_id, str):
			self.m_current_station = int(current_id)
		elif isinstance(current_id, int):
			self.m_current_station = current_id
		else:
			raise ValueError("current_id should be integer type")
		self.dom.find('current_station').text = str(self.m_current_station)
		return self.m_current_station

	def current_station(self):
		"""
		get the id of the currently selected station
		"""
		return self.m_current_station
	
	def persist(self):
		print ('persisting data model')
		self.dom.write(PARADIUM_VHOME + 'data.xml')
		return
	
	

if __name__ == '__main__':

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	filehandler = logging.handlers.TimedRotatingFileHandler('./paradium.log', when='midnight', interval=1, backupCount=10)
	filehandler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
	logger.addHandler(filehandler)

	# setup environment variable defaults
	PARADIUM_HOME     = '/opt/paradium/'
	PARADIUM_VHOME    = '/var/paradium/'
	PARADIUM_MPDHOST  = '127.0.0.1'

	# and override with the actual environment
	if 'PARADIUM_HOME' in os.environ:
		PARADIUM_HOME = os.environ['PARADIUM_HOME']
	if 'PARADIUM_MPDHOST' in os.environ:
		PARADIUM_MPDHOST = os.environ['PARADIUM_MPDHOST']


	dm = DataModel(logger)
	
	dm.set_current_station(42)

	dm.persist()
	
	print ('Current: {}'.format(dm.current_station()))
	