#
# vban.py configuration file
#

# for future use
default_priority = 5

# max retries before giving up on a ban
max_tries = 3

# mongodb URL
db_addr = 'mongodb://user:passwd@mongodb_srv.company.com:27017/vban'

# vnid: hostname
srvlist = { 	'int01': 'internal01.comapny.com',
		'int02': 'internal02.company.com',
		'par01': 'paris01.company.com',
		'par02': 'paris02.company.com',
		'mrs01': 'marseille01.company.com',
		'lyn01': 'lyon01.company.com',
          }


# passphrase
ban_key = 'big_random_string'

syslog_facility = syslog.LOG_LOCAL3
syslog_priority = syslog.LOG_INFO

pidfile = "/var/run/vbaner.pid"
