#
# vban.py configuration file
#

# for future use
default_priority = 5

# max retries before giving up on a ban
max_tries = 3

# mongodb URL
db_addr = 'mongodb://user:passwd@mongodb_srv.company.com:27017/vban'

# mapping between mongodb attribute and varnish HTTP pseudo-header
fk_map = { 'companyId': 'X-VE-FK-CompanyID',
           'site': 'X-VE-Site',
           'matchRule': 'X-VE-MatchedRule',
	   'vsClientId': 'X-VE-DS-ClientID',
	   'url': 'X-URL'
         }

# array of dicts for each server, with tags
srvlist = ( { 'alias': 'int01', 'hostname': 'internal01.company.com',  'target': ( 'internal' ) },
            { 'alias': 'int02', 'hostname': 'internal02.company.com',  'target': ( 'internal' ) },
            { 'alias': 'par01', 'hostname': 'paris01.company.com',     'target': ('external', 'paris') },
            { 'alias': 'par02', 'hostname': 'paris02.company.com',     'target': ('external', 'paris') },
            { 'alias': 'mrs01', 'hostname': 'marseille01.company.com', 'target': ('external', 'marseille' ) },
            { 'alias': 'lyn01', 'hostname': 'lyon01.company.com',      'target': ('external', 'marseille' ) },
          )
            
ban_key = ''

syslog_facility = syslog.LOG_LOCAL3
syslog_priority = syslog.LOG_INFO

pidfile = "/var/run/vbaner.pid"
