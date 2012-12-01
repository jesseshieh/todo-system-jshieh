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
      # tasks gets added to the front of the list.  grab the last one.
      # skip empty tasks
      for t in reversed(tasks):
        if t['title']:
          task = t
          break


    template_values = {
      'task': task,
      'contexts': contexts,
      'context': context,
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.headers.add_header('Set-Cookie', str('context=%s;' % context['id']))
    self.response.out.write(template.render(path, template_values))
  
  @decorator.oauth_required
  def post(self):
    service = build('tasks', 'v1', http=decorator.http())
    name = self.request.get("name")
    context = self.request.get("context")
    service.tasks().insert(tasklist=context, body={
      'title': name,
    }).execute()
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

