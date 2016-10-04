#!/usr/bin/python3.2

#
# Virtual Expo Varnish AutoBan Manager - Thomas Lecomte
#
# Push bans on a farm of Varnish servers, imported from a MongoDB database.
#

from datetime import datetime
import threading
import pymongo
import socket
import http.client
import signal, os
import time
import sys
import argparse
import syslog

# debug
import code

class StsThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StsThread, self).__init__(*args, **kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        super(StsThread, self).join(*args, **kwargs)

        return self._return

# source the configuration
with open(os.path.dirname(sys.argv[0]) + '/conf.py') as f:
    code = compile(f.read(), "conf.py", 'exec')
    exec(code)

# global variables
client = bans = new_requests = 0
running = True

# CLI arguments
args = False

def log(msg):
        if args.stdout and args.nodaemon:
                print("[%s] %s" % (str(datetime.now()), msg))
        else:
                syslog.syslog(args.priority, "[%s] %s" % (str(datetime.now()), msg))

def handle_new_req():
        global running
        global new_requests
        global bans

        while running:
                time.sleep(1)
                try:
                        for req in new_requests.find():
                                servers_pending = { }
                                request_id = req['_id']
                                del req['_id']
                                if 'origin' in req:
                                  origin = req['origin']
                                  del req['origin']
                                else:
                                  origin = 'backoffice'

                                if 'priority' in req:
                                  priority = req['priority']
                                  del req['priority']
                                else:
                                  priority = default_priority

                                if 'target' in req:
                                  target = req['target']
                                  del req['target']
                                else:
                                  target = 'html'

                                for s in srvlist:
                                  if target in s['target']:
                                    servers_pending[s['alias']] = 'PENDING'

                                if bans.find({ 'parameters': req, 'status': 'pending' }).count() > 0:
                                        log ( "[%s] duplicate, ignoring" % ( request_id ) )
                                        new_requests.remove({ '_id': request_id })
                                        continue

                                # we remove it before inserting the ban
                                # since it's not atomic, if the connection is dropped
                                # we avoid a duplicate key error
                                new_requests.remove( { '_id': request_id } )
                                newban_id = bans.insert({        '_id': request_id,
                                                                'status': 'pending',
                                                                'parameters': req,
                                                                'extendedStatus': servers_pending,
                                                                'priority': priority,
                                                                'origin': origin,
                                                                'tries': 0,
                                                                'target': target,
                                                                'createdAt': datetime.utcnow()
                                                }, manipulate=True, j=True)
                                log( "[%s -> %s] priority:%s" % (request_id, newban_id, priority) )

                except pymongo.errors.OperationFailure as e:
                        log( e.details )
                        log( 'import_thread: mongodb query failed, retrying.' )
                except pymongo.errors.AutoReconnect:
                        log( 'import_thread: lost connection, reconnecting in 5 seconds' )
                        time.sleep(5)
                except:
                        if not running: break
                        else: raise


def set_ban_status(ban, status):
        log ( "[%s] status: %s" % (ban['_id'], status) )
        bans.update( { '_id': ban['_id'] }, { "$set": { "status": status } })

def set_ban_extended_status(ban, srv, status):
        #log ( "[%s] extended_status: %s=%s" % (ban['_id'], srv, status) )
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

def do_ban(host, ban_str, target):
        try:
                http_conn = http.client.HTTPConnection(host, 80, timeout=5)
                http_conn.putrequest("VEBAN", "/")
                http_conn.putheader('X-VE-BanKey', ban_key)
                http_conn.putheader('X-VE-BanTarget', target)
                http_conn.putheader('X-VE-BanStr', ban_str)
                http_conn.endheaders()
                response = http_conn.getresponse()
                return response.status
        except (http.client.HTTPException, socket.error, socket.timeout) as ex:
                return 503

def how_many_srvs(target):
  i = 0
  for s in srvlist:
    if s['target'] == target:
      i += 1
  return i

def handle_ban(ban):
        ban_on = { }
        for s in srvlist:
          if ban['target'] in s['target']:
            ban_on[s['alias']] = s['hostname']

        set_ban_status(ban, "processing")

        # remove servers where the ban has already been applied
        for srv in ban['extendedStatus']:
                if srv in ban['extendedStatus'] and ban['extendedStatus'][srv] == "OK":
                        try:        del ban_on[srv]
                        except:        log( "WARNING: server %s no longer exists" % srv )

        ban_str = ""

        for param in ban['parameters']:
                if param in [ '_id', '_class' ]: continue
                try: fk = fk_map[param]
                except:
                        log( "[%s] unknown parameter %s in fk_map - ignoring ban" % (ban['_id'], param) )
                        set_ban_status(ban, "invalid")
                        return
                        
                if ban_str != "": ban_str += ' && '
                ban_str += 'obj.http.' + fk + ' == ' + str(ban['parameters'][param])
        
        target = ban['target']

        log ( "[%s] ban_str: %s" % ( ban['_id'], ban_str ) )

        increment_ban_tries(ban)
        log ( "[%s] try %i/%i" % ( ban['_id'], get_ban_tries(ban), max_tries) )

        err = 0
        ban_threads = []

        for srv in ban_on:
                th = StsThread(target=do_ban, args=(ban_on[srv], ban_str, target))
                th.daemon = True
                th.name = srv
                ban_threads.append(th)
                th.start()

        output = "[%s] ext_sts: " % ban['_id']
        for th in ban_threads:
                ret = th.join()
                if ret == 200:
                        set_ban_extended_status(ban, th.name, "OK")
                        output += " %s/OK" % th.name
                else:
                        set_ban_extended_status(ban, th.name, "FAIL/[err=%i]" % ret)
                        output += " %s/FAIL" % th.name
                        err += 1

        log ( output )

        if err == 0:                        set_ban_status(ban, "completed")
        elif get_ban_tries(ban) >= max_tries:
                if err == how_many_srvs(ban['target']):        set_ban_status(ban, "full-fail")
                else:                                        set_ban_status(ban, "partial-fail")
        else: set_ban_status(ban, "wait-for-retry")

def intr_handler(signum, frame):
        log( "signal %s caught" % signum )
        global running
        running = False

def connect():
        while True:
                try: client = pymongo.MongoClient(db_addr, socketTimeoutMS=10000, connectTimeoutMS=5000, replSet=repl_set)
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
                print('unable to write pid file')

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

        newreq_t = threading.Thread(target=handle_new_req)
        newreq_t.daemon = True
        newreq_t.start()

        while running:
                try:
                        for doc in bans.find({ 'status': { "$in": [ 'pending', 'processing', 'wait-for-retry' ] } } ).sort([ ('priority', -1), ('createdAt', 1) ]).limit(1):
                                if not running: break
                                handle_ban(doc)
                except pymongo.errors.OperationFailure as e:
                        log( e.details )
                        log( 'ban_thread: mongodb query failed, retrying.' )
                except pymongo.errors.AutoReconnect:
                        log( 'ban_thread: lost connection, reconnecting in 5 seconds' )
                        time.sleep(5)
                except:
                        if not running: break
                        else: raise

                time.sleep(1)

        newreq_t.join()
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
                print("daemon is already running")
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
