#!/usr/bin/python2.7

#
# Virtual Expo Varnish AutoBan Manager - Thomas Lecomte
#
# Push bans on a farm of Varnish servers, imported from a MongoDB database.
#

from datetime import datetime
import pymongo
import httplib
import signal, os
import time
import sys
import argparse
import syslog

# debug
import code

# source the configuration
execfile(os.path.dirname(sys.argv[0]) + '/conf.py')

# global variables
client = bans = new_requests = 0
running = True

# mapping between mongodb attribute and varnish HTTP pseudo-header
fk_map = { 'companyId': 'X-VE-FK-CompanyID',
           'site': 'X-VE-Site'
         }

# CLI arguments
args = False

def log(msg):
	if args.stdout and args.nodaemon:
		print "[%s] %s" % (str(datetime.now()), msg)
	else:
		syslog.syslog(args.priority, "[%s] %s" % (str(datetime.now()), msg))

def handle_new_req(req):
	servers_pending = { }
	for s in srvlist: servers_pending[s] = 'PENDING'
	request_id = req['_id']
        del req['_id']
	if 'origin' in req:
          origin = req['origin']
          del req['origin']
	else:
	  origin = 'backoffice'

	newban_id = bans.insert({	'_id': request_id,
					'status': 'pending',
					'parameters': req,
					'extendedStatus': servers_pending,
					'priority': default_priority,
					'origin': origin,
					'tries': 0,
					'createdAt': datetime.utcnow()
			}, manipulate=True, j=True)

	new_requests.remove( { '_id': request_id } )
	log( "reqid:%s imported as %s" % (request_id, newban_id) )

def set_ban_status(ban, status):
	log ( "[%s] status: %s" % (ban['_id'], status) )
	bans.update( { '_id': ban['_id'] }, { "$set": { "status": status } })

def set_ban_extended_status(ban, srv, status):
	log ( "[%s] extended_status: %s=%s" % (ban['_id'], srv, status) )
	ban2 = bans.find_one( { '_id': ban['_id'] } )
	sts = ban2['extendedStatus'].copy()
	sts[srv] = status
	bans.update({ '_id': ban['_id'] }, { "$set": { "extendedStatus": sts } } )
	#sys.exit(0)

def get_ban_tries(ban):
	try: return bans.find_one({ '_id': ban['_id'] } )['tries']
        except: return 0

def increment_ban_tries(ban):
	bans.update({ '_id': ban['_id'] }, { "$inc": { "tries": 1 } } )

def do_ban(host, ban_str):
	http = httplib.HTTPConnection(host, 80, timeout=5)
	http.putrequest("VEBAN", "/")
	http.putheader('X-VE-BanKey', ban_key)
	http.putheader('X-VE-BanTarget', 'html')
	http.putheader('X-VE-BanStr', ban_str)
	http.endheaders()
	response = http.getresponse()

	return response.status

def handle_ban(ban):
	ban_on = srvlist.copy()

	set_ban_status(ban, "processing")

	# remove servers where the ban has already been applied
	for srv in ban['extendedStatus']:
		if srv in ban['extendedStatus'] and ban['extendedStatus'][srv] == "OK":
			try:	del ban_on[srv]
			except:	log( "WARNING: server %s no longer exists" % srv )

	ban_str = ""

	for param in ban['parameters']:
		if param == '_id': continue
		try: fk = fk_map[param]
		except:
			log( "[%s] unknown parameter %s in fk_map - ignoring ban" % (ban['_id'], param) )
			set_ban_status(ban, "invalid")
			return
			
		if ban_str != "": ban_str += ' && '
		ban_str += 'req.http.' + fk + ' == ' + str(ban['parameters'][param])

	log ( "[%s] ban_str: %s" % ( ban['_id'], ban_str ) )

        increment_ban_tries(ban)
	log ( "[%s] try %i/%i" % ( ban['_id'], get_ban_tries(ban), max_tries) )

	err = 0
	for srv in ban_on:
		ret = do_ban(ban_on[srv], ban_str)
		if ret == 200:
			set_ban_extended_status(ban, srv, "OK")
		else:
			set_ban_extended_status(ban, srv, "FAIL/[err=%i]" % ret)
			err += 1

	if err == 0:			set_ban_status(ban, "completed")
	elif get_ban_tries(ban) >= max_tries:
		if err == len(srvlist):	set_ban_status(ban, "full-fail")
		else:			set_ban_status(ban, "partial-fail")
	else: set_ban_status(ban, "wait-for-retry")

def intr_handler(signum, frame):
	log( "signal %s caught" % signum )
	global running
	running = False

def connect():
	while True:
		try: client = pymongo.MongoClient(db_addr, socketTimeoutMS=10000, connectTimeoutMS=5000)
		except pymongo.errors.ConnectionFailure as e:
			log( 'unable to connect to %s, retrying in 5 seconds' % (db_addr) )
		else:
			log ( 'connected to %s' % (client.host) )
			break
		time.sleep(5)
	return client

def write_pid_file():
	try:
		f = open(pidfile, 'w')
		f.write(str(os.getpid()))
		f.close()
	except:
		print 'unable to write pid file'

def cleanup():
	log( "cleaning up" )
	client.disconnect()


def vbaner():
	global running, args
	global client, new_requests, bans

	log( "vbaner starting [pid=%i]" % os.getpid() )

	client = connect()
	bans = client.vban.bans
	new_requests = client.vban.new_requests

	signal.signal(signal.SIGINT, intr_handler)
	signal.signal(signal.SIGTERM, intr_handler)

	running = True

	while running:
		try:
			for doc in new_requests.find():
				handle_new_req(doc)
			for doc in bans.find({ 'status': { "$in": [ 'pending', 'processing', 'wait-for-retry' ] } } ):
				handle_ban(doc)
		except pymongo.errors.OperationFailure as e:
			log( e.details )
			log( 'mongodb query failed, aborting.' )
			running = False
		except pymongo.errors.AutoReconnect:
			log( 'lost connection, reconnecting in 5 seconds' )
			time.sleep(5)
		except:
			if not running: break
			else: raise

		time.sleep(1)

	cleanup()

def check_running():
	if os.path.isfile(pidfile):
		pid = open(pidfile, 'r').readline()
		try: os.kill(int(pid), 0)
		except OSError: return False
		else: return True
	return False

def main():
	global args

	parser = argparse.ArgumentParser(description='Virtual Expo Varnish AutoBan manager')
	parser.add_argument('--nodaemon', action='store_true', help='stay in foreground')
	parser.add_argument('--stdout',   action='store_true', help='log to stdout instead of syslog')
	parser.add_argument('--facility', nargs=1, default=syslog_facility, help='syslog facility to log to')
	parser.add_argument('--priority', nargs=1, default=syslog_priority, help='syslog priority to use')

        if check_running():
        	print "daemon is already running"
		sys.exit(1)

	args = parser.parse_args()

	if args.stdout == False:
		syslog.openlog(facility=args.facility)

	if args.nodaemon == False:
		if os.fork():
			sys.exit(1)


	write_pid_file()

	while True:
		try:
			vbaner()
			break  # normal exit
		except:
			if args.nodaemon:
				raise
				break
			else:
				log( "CRITICAL: exception caught - restarting in 5 seconds" )
				time.sleep(5)
				cleanup()

	if args.stdout == False: syslog.closelog()

	try: os.unlink(pidfile)
	except: log( "unable to remove pidfile %s" % pidfile )

	log( "done, exiting" )



if __name__ == "__main__":
	main()