#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import cgi
import datetime
import urllib
import webapp2
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import time
from rfc3339 import rfc3339

from google.appengine.ext import db
from google.appengine.api import users
import os
from google.appengine.ext.webapp import template

from apiclient.discovery import build
import httplib2
from oauth2client.appengine import OAuth2Decorator
import settings

decorator = OAuth2Decorator(client_id=settings.CLIENT_ID,
                            client_secret=settings.CLIENT_SECRET,
                            scope=settings.SCOPE,
                            user_agent='todo-system-jshieh')

class Context(db.Model):
  creation_time = db.DateTimeProperty(auto_now_add=True)
  last_modified_time = db.DateTimeProperty(auto_now=True)
  name = db.StringProperty(required=True)

class Task(db.Model):
  creation_time = db.DateTimeProperty(auto_now_add=True)
  last_modified_time = db.DateTimeProperty(auto_now=True)
  context = db.ReferenceProperty(db.Model, required=False)
  name = db.StringProperty(required=True)
  complete = db.BooleanProperty(default=False)

class MainHandler(webapp2.RequestHandler):
	
  @decorator.oauth_required
  def get(self):
    service = build('tasks', 'v1', http=decorator.http())

    result = service.tasklists().list().execute()
    contexts = result.get('items', [])

    context_param = self.request.get('context') or self.request.cookies.get('context') or '@default'
    context = service.tasklists().get(tasklist=context_param).execute()

    result = service.tasks().list(tasklist=context['id'], showCompleted=False, showDeleted=False, showHidden=False).execute()
    tasks = result.get('items', [])
    task = {}
    if tasks:
      task = tasks[0]

    template_values = {
      'task': task,
      'contexts': contexts,
      'context': context,
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.headers.add_header('Set-Cookie', str('context=%s;' % context['id']))
    self.response.out.write(template.render(path, template_values))
  
  def post(self):
    name = self.request.get("name")
    task = Task(name=name)
    task.put()
    self.redirect('/')

class CompleteHandler(webapp2.RequestHandler):
  @decorator.oauth_required
  def get(self):
    service = build('tasks', 'v1', http=decorator.http())
    task = self.request.get('task')
    context = self.request.get('context')

    service.tasks().delete(tasklist=context, task=task).execute()

    self.redirect('/')

class MoveHandler(webapp2.RequestHandler):
  @decorator.oauth_required
  def get(self):
    service = build('tasks', 'v1', http=decorator.http())
    task = self.request.get('task')
    context = self.request.get('context')
    destination_context = self.request.get('destination_context')

    # copy it over
    body = service.tasks().get(tasklist=context, task=task).execute()
    service.tasks().insert(tasklist=destination_context, body={
      'title': body['title'],
    }).execute()

    # complete it
    service.tasks().delete(tasklist=context, task=task).execute()

    self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/complete', CompleteHandler),
    ('/move', MoveHandler),
    (decorator.callback_path, decorator.callback_handler()),
], debug=True)

