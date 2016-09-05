#!/usr/bin/python3.2

import os
import bottle
import pymongo
import pprint
import time
import datetime
from time import sleep
from bson.objectid import ObjectId
from bottle import Bottle, template, static_file, post, request, redirect

os.chdir(os.path.dirname(__file__))

#### vars
db_addr = 'mongodb://user:passwd@server.company.com:27017/vban'

client = None
bans = None
new_requests = None

#### init

def setup_routing():
  application.route('/', 'GET', bans_view)
  application.route('/bans/view', 'GET', bans_view)
  application.route('/bans/add', 'GET', bans_add)
  application.route('/ban/submit', 'POST', ban_submit)
  application.route('/ban/details/<ban_id>', 'GET', ban_details)
  application.route('/static/<filename>', 'GET', static)
  application.route('/bans/varnish', 'GET', bans_varnish)

def open_db():
  global client, bans, new_requests
  client = pymongo.MongoClient(db_addr, socketTimeoutMS=10000, connectTimeoutMS=5000)
  bans = client.vban.bans
  new_requests = client.vban.new_requests

def close_db():
  global client
  client.close()

#### routes

def bans_view():
    global bans
    global new_requests
    open_db()
    ban_list = bans.find().sort('createdAt', pymongo.DESCENDING)
    close_db()
    if 'items' in request.query:
      items = request.query['items']
    else:
      items = '100'
    new_requests_count = new_requests.find().count()
    return template('bans_view.tpl', ban_list=ban_list, items=items, new_requests_count=new_requests_count)

def bans_add():
    return template('bans_add.tpl')

def ban_submit():
    global new_requests

    ban_type = request.forms.get('ban-type')

    mrid = request.forms.get('matchRule')
    site = request.forms.get('site')
    companyId = request.forms.get('companyId')
    target = request.forms.get('target')
    vsClientId = request.forms.get('vsClientId')
    url = request.forms.get('url')

    doc = { "origin": "vbaner/"+request.environ.get('REMOTE_ADDR'), "priority": 10 }

    for attr in [ 'matchRule', 'site', 'companyId', 'target', 'url', 'vsClientId', 'subdomain' ]:
        val = request.forms.get(attr)
        if not val: continue
        if len(val) > 0:
            doc[attr] = val

    if len(doc) < 2:
        redirect("/ban/msg/?err=42")
        return

    # insert the ban request
    open_db()
    ban_id = new_requests.insert( doc )
    close_db()
    # wait for the ban to be processed
    sleep(1)
    redirect("/ban/details/" + str(ban_id))

def ban_details(ban_id):
    global bans
    open_db()
    try:
      ban = bans.find_one({ '_id': ObjectId(ban_id) })
    except:
      return template('error.tpl', error="invalid ban id")
    if ban == None:
      return template('error.tpl', error="ban not found")
    close_db()
    return template('ban_details.tpl', ban=ban)
    
def bans_varnish():
    return template('error.tpl', error='not implemented (yet).')

def static(filename):
    return static_file(filename, os.path.dirname(__file__) + '/static')

#### app

application = bottle.default_app()
setup_routing()
