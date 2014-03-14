#!/usr/bin/python3

import string,time
import sys,os
from daemon import Daemon

from http.server import SimpleHTTPRequestHandler 
import socketserver
import logging
import logging.handlers
from urllib.parse import urlparse, parse_qs, unquote
from subprocess import call
from mpd import MPDClient

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
filehandler = logging.handlers.TimedRotatingFileHandler('/tmp/paradium.log', when='midnight', interval=1, backupCount=10)
filehandler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(filehandler)

# setup environment variables
PARADIUM_HOME    = '/opt/paradium'
PARADIUM_MPDHOST = '127.0.0.1'
if 'PARADIUM_HOME' in os.environ:
	PARADIUM_HOME = os.environ['PARADIUM_HOME']
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


def do_play():
	print ("they want me to play")
	client.play()

	return

def do_stop():
	print ("they want me to stop playing")
	client.stop()
	return

def do_shutdown():
	call("/sbin/halt")
	return


class ParadiumHandler(SimpleHTTPRequestHandler):

	def handle_current_song(self):
		self.send_response(200)
		self.send_header(b"Content-type", b"text/html")
		self.end_headers()
		self.wfile.write(bytes(client.currentsong().get('title'), 'UTF-8'))
		return

	def handle_current_station(self):
		# get what's playing
		self.send_response(200)
		self.send_header(b"Content-type", b"text/html")
		self.end_headers()
		self.wfile.write(b"Radio Paradise")
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
				elif command == 'stop':
					do_stop()
				elif command == 'shutdown':
					do_shutdown()
				else:
					self.send_error(404, b"Unknown command: %s" % command)
					return

				# After processing the command I redirect back to the index page.
				self.send_response(200)
				self.send_header(b"Content-type", b"text/html")
				self.end_headers()
				self.wfile.write(b"<!DOCTYPE html><html><head>")
				#self.wfile.write(b"<meta http-equiv=\"Refresh\" Content=\"0; URL=/\">")
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



class ParadiumServer(Daemon):
	"""
	server wrapper
	"""

	def run(self):
		try:
			port = 80
			httpd = socketserver.TCPServer(("", port), ParadiumHandler)
			
			httpd.allow_reuse_address = True
			print('started httpserver, listening...')
	
			httpd.serve_forever()

			print('loop done...')

		except KeyboardInterrupt:
			print('^C received, shutting down server')
			httpd.socket.close()

		return



if __name__ == '__main__':
	daemon = ParadiumServer('/tmp/paradium-daemon.pid')
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
		logger.warning('show cmd deamon usage')
		print ("Usage: {} start|stop|foreground|restart".format(sys.argv[0]))
		sys.exit(2)
 
