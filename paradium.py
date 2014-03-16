#!/usr/bin/python3

import string,time
import sys, os
from daemon import Daemon

from http.server import HTTPServer, SimpleHTTPRequestHandler 
import socketserver
import logging
import logging.handlers
from urllib.parse import urlparse, parse_qs, unquote
from subprocess import call
from stations import Station, Stations
from datamodel import DataModel
from mpd import MPDClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
filehandler = logging.handlers.TimedRotatingFileHandler('/tmp/paradium.log', when='midnight', interval=1, backupCount=10)
filehandler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(filehandler)

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

# setup global MPD client object
client = MPDClient()
client.connect(PARADIUM_MPDHOST, 6600)

# modify this to add additional routes
ROUTES = (
    # [url_prefix ,  directory_path]
    ['/media', '/var/www/media'],
    ['', PARADIUM_HOME + '/htdocs']  # empty string for the 'default' match
) 

# read radio stations file and make available
stations = Stations(logger);

# Now here's the thing. A solid way to handle our data 
# model would be to have it owned by the daemon and pass
# a reference into the ParadiumHandler to deal with 
# everything that comes in. Alas, I cannot do this as it
# looks like python wouldn't have a way to pass an additional
# parameter at class creation as this is done by the underlying
# http.server
# So for now I have it global and see how I go
dm = DataModel(logger)

def play_current():
	"""
	try to play the station currently selected in our data model no matter what
	"""
	s = stations.get_station(dm.current_station())
	client.stop()
	client.clear()
	for url in s.urls:
		print('adding ' + url)
		client.add(url)
	client.play()
	return

def do_play():
	client.play()
	return

def do_prev():
	s = stations.get_prev(dm.current_station())
	dm.set_current_station(s.id)
	play_current()
	return

def do_next():
	s = stations.get_next(dm.current_station())
	dm.set_current_station(s.id)
	play_current()
	return

def do_stop():
	print ("they want me to stop playing")
	client.stop()
	return

def do_shutdown():
	call("/sbin/halt")
	return


class ParadiumHandler(SimpleHTTPRequestHandler):
	"""
	Handle incoming HTTP request and pass everything 
	I don't know to underlying base.
	
	Not that an instance of this object is being created
	every time a request comes in
	"""
		
	def handle_current_song(self):
		self.send_response(200)
		self.send_header(b"Content-type", b"text/html")
		self.end_headers()
		title = client.currentsong().get('title')
		if not title:
			title = "none"
		self.wfile.write(bytes(title, 'utf-8'))
		return

	def handle_current_station(self):
		# get what's playing in dynamic data DataModel
		cs = dm.current_station()
		
		# the id would refer to an actual station
		station = stations.get_station(cs)

		if station is None:
			desc = 'Not tuned in'
		else:
			if station.website:
				desc = '<a href=\"{0}\">{1}</a>'.format(station.website, station.name)
			else:
				desc = station.name
			
		self.send_response(200)
		self.send_header(b"Content-type", b"text/html")
		self.end_headers()
		self.wfile.write(bytes(desc, 'utf-8'))
		return

	def do_GET(self):

		logger.info('GET received: {}'.format(self.path))
		
		try:
			# first parse the url
			# returns a 6-tuple
			url = urlparse(self.path) 
			path = url[2]

			# now dispatch
			if path == '/paradium.html':
				query = parse_qs(url[4])
				command = query.get('command', [0])[0]
				logger.info('paradium executing command: {}'.format(command))
				
				if command == 'play':
					do_play()
				elif command == 'prev':
					do_prev()
				elif command == 'next':
					do_next()
				elif command == 'stop':
					do_stop()
				elif command == 'shutdown':
					do_shutdown()
				else:
					self.send_error(404, b"Unknown command: %s" % command)
					return

				# After processing the command I just send an OK. It's gonna be ignored anyway
				self.send_response(200)
				self.send_header(b"Content-type", b"text/html")
				self.end_headers()
				self.wfile.write(b"<!DOCTYPE html><html><head>")
				self.wfile.write(b"</head><body>done</body></html>")
				return
			elif path == '/current_song.html':
				self.handle_current_song()
				return
			elif path == '/current_station.html':
				self.handle_current_station()
				return
			else:
				super(ParadiumHandler, self).do_GET()
				return
			return

		except IOError:
			self.send_error(404, b"File Not Found: %s" % self.path)
		except ValueError:
			self.send_error(403, b"WTF is this?: %s" % self.path)

	def translate_path(self, path):
		"""translate path given routes"""

		# set default root to cwd
		root = os.getcwd()
        
		# look up routes and set root directory accordingly
		for pattern, rootdir in ROUTES:
			if path.startswith(pattern):
				# found match!
				path = path[len(pattern):]  # consume path up to pattern len
				root = rootdir
				break
       
		# first parse the url
		# returns a 6-tuple
		url = urlparse(self.path) 

		# now dispatch
		path = url[2]

		# normalize path and prepend root directory
		path = os.path.normpath(unquote(path))
		words = path.split('/')
		words = filter(None, words)
        
		path = root
		for word in words:
			drive, word = os.path.splitdrive(word)
			head, word = os.path.split(word)
			if word in (os.curdir, os.pardir):
				continue
			path = os.path.join(path, word)

		return path



class ParadiumServer(HTTPServer):
	"""
	TCP server overload to reuse address and stuff
	"""
	
	def __init__(self, bind_address = "", port = 8080):
	
		# read user data object
		dm = DataModel(logger)

		# Initialize server itself
		self.allow_reuse_address = True
		HTTPServer.__init__(self, (bind_address, port), ParadiumHandler)

		return

	def stop(self):
		self.m_dm.persist()
		return


class ParadiumDaemon(Daemon):
	"""
	daemon wrapper
	"""

	def run(self):
		try:
			self.tmp_server = ParadiumServer("")
			print('started httpserver, listening...')
			self.tmp_server.serve_forever()
			print('loop done...')

		except KeyboardInterrupt:
			print('^C received, shutting down server')
			self.tmp_server.socket.close()
			self.tmp_server.stop()
		return

	def stop(self):
		self.tmp_server.stop()
		Daemon.stop(self)
		return


if __name__ == '__main__':
	daemon = ParadiumDaemon('/tmp/paradium-daemon.pid')
	if len(sys.argv) == 2:
		logger.info('{} {}'.format(sys.argv[0],sys.argv[1]))
 
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'foreground' == sys.argv[1]:
			daemon.run()
		else:
			print ("Unknown command")
			sys.exit(2)
		sys.exit(0)
	else:
		logger.warning('show cmd daemon usage')
		print ("Usage: {} start|stop|foreground|restart".format(sys.argv[0]))
		sys.exit(2)
 
