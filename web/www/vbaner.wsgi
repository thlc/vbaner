#!/usr/bin/python

import os
import bottle
import pymongo
import pprint
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
  client.disconnect()

#### routes

def bans_view():
    global bans
    open_db()
    ban_list = bans.find()
    close_db()
    return template('bans_view.tpl', ban_list=ban_list)

def bans_add():
    return template('bans_add.tpl')

def ban_submit():
    global new_requests

    ban_type = request.forms.get('ban-type')

    if ban_type == 'purge-by-matchrule':
        mrid = request.forms.get('matchRule')
        doc = { "matchRule": mrid, "origin": "vbaner/"+request.environ.get('REMOTE_ADDR') }

    elif ban_type == 'purge-by-companyd':
        companyId = request.forms.get('companyId')
        site = request.forms.get('site')
        doc = { "site": site, "companyId": companyId, "origin": "vbaner/"+request.environ.get('REMOTE_ADDR') }

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
