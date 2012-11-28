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
import cgi
import datetime
import urllib
import webapp2

from google.appengine.ext import db
from google.appengine.api import users
import os
from google.appengine.ext.webapp import template


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
  def get(self):
    user = users.get_current_user()
    context = self.request.get('context') 
    if context:
      context = int(context)
      context = Context.get_by_id(context)
    else:
      context = None

    query = Task.all().filter('complete =', False).order('creation_time')
    if context:
      query.filter('context = ', context)
    task = query.get()
    contexts = Context.all()
    template_values = {
      'task': task,
      'contexts': contexts,
      'context': context,
      'user': user,
      'logout_url': users.create_logout_url('/'),
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
  
  def post(self):
    name = self.request.get("name")
    task = Task(name=name)
    task.put()
    self.redirect('/')

class CompleteHandler(webapp2.RequestHandler):
  def get(self):
    task = self.request.get('task')
    task = int(task)
    task = Task.get_by_id(task)
    task.complete = True
    task.put()
    self.redirect('/')

class MoveHandler(webapp2.RequestHandler):
  def get(self):
    task = self.request.get('task')
    context = self.request.get('context')
    task = int(task)
    context = int(context)
    task = Task.get_by_id(task)
    context = Context.get_by_id(context)
    task.context = context
    task.put()
    self.redirect('/')

class CreateContextHandler(webapp2.RequestHandler):
  def get(self):
    name = self.request.get('name')
    context = Context(name=name)
    context.put()
    self.response.out.write('created context with name ' + name)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/complete', CompleteHandler),
    ('/move', MoveHandler),
    ('/create_context', CreateContextHandler),
], debug=True)

