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
# TODO: All python code is in this place for larger apps we need to
# separate it.
import os
import webapp2
import jinja2
import json
import webob

from webapp2_extras.appengine.auth.models import User
from webapp2_extras import sessions
from google.appengine.ext import db

from wtforms.form import Form
from wtforms import fields
from wtforms import validators


class Message(db.Model):
    sender = db.EmailProperty()
    recipient = db.EmailProperty()
    body = db.TextProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)


class UserForm(Form):
    full_name = fields.StringField(u'Full Name', validators=[validators.input_required()])
    email = fields.StringField(u'Email', validators=[validators.input_required(), validators.Email()])
    password = fields.PasswordField(u'Password', validators=[validators.input_required()])


class MessageForm(Form):
    sender = fields.StringField(u'Sender', validators=[validators.input_required(), validators.Email()])
    recipient = fields.StringField(u'Recipient', validators=[validators.input_required(), validators.Email()])
    body = fields.TextField(u'Body', validators=[validators.input_required()])


class LoginForm(Form):
    email = fields.StringField(u'Email', validators=[validators.input_required(), validators.Email()])
    password = fields.PasswordField(u'Password', validators=[validators.input_required()])


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

    @webapp2.cached_property
    def user(self):
        auth_id = self.session.get('user', None)
        if auth_id:
            return User.get_by_auth_id(auth_id)


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(BaseHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({'user': self.user}))


class TemplateHandler(BaseHandler):
    def get(self, template_name):
        template = JINJA_ENVIRONMENT.get_template('templates/%s' % template_name)
        self.response.write(template.render({'user': self.user}))


class MessageHandler(BaseHandler):
    def get(self, _id=None):
        if self.user:
            q = Message.gql('WHERE sender=:email', email=self.user.auth_ids[0])
            response = [{'sender': message.sender, 'recipient': message.recipient, 'body': message.body} for message in q]

            q = Message.gql('WHERE recipient=:email', email=self.user.auth_ids[0])
            response.extend([{'sender': message.sender, 'recipient': message.recipient, 'body': message.body} for message in q])
            self.response.headers.add_header('Content-Type', 'application/json')
            self.response.write(json.dumps(response))
        else:
            self.response.set_status(403)

    def post(self):
        # set headers
        # Just simple validation, this is not validating if user exists... just create the message
        self.response.headers.add_header('Content-Type', 'application/json')
        form = MessageForm(formdata=webob.multidict.MultiDict(json.loads(self.request.body or '{}')))
        form.validate()
        if form.errors:
            self.response.set_status(400)
            self.response.write(json.dumps(form.errors))
        else:
            m = Message(sender=form.sender.data, recipient=form.recipient.data, body=form.body.data)
            m.put()
            self.response.set_status(201)


class UserHandler(BaseHandler):
    def get(self, _id=None):
        if self.user:
            q = User.gql('')
            response = [{'email': user.auth_ids[0], 'fullname': user.full_name} for user in q]
            self.response.headers.add_header('Content-Type', 'application/json')
            self.response.write(json.dumps(response))
        else:
            self.response.set_status(403)

    def post(self):
        # set headers
        self.response.headers.add_header('Content-Type', 'application/json')
        form = UserForm(formdata=webob.multidict.MultiDict(json.loads(self.request.body or '{}')))
        form.validate()
        if form.errors:
            self.response.set_status(400)
            self.response.write(json.dumps(form.errors))
        else:
            created, info = User.create_user(form.email.data, password_raw=form.password.data, full_name=form.full_name.data)
            if created:
                self.response.set_status(201)
            else:
                self.response.set_status(400)
                errors = {
                    'auth_id': {
                        'key': 'email',
                        'msg': 'Email is already registered'
                    }
                }
                duplicates = {}
                for item in info:
                    duplicates[errors[item]['key']] = errors[item]['msg']
                self.response.write(json.dumps(duplicates))


class LoginHandler(BaseHandler):
    def get(self, _id=None):
        pass

    def post(self):
        # set headers
        self.response.headers.add_header('Content-Type', 'application/json')
        form = LoginForm(formdata=webob.multidict.MultiDict(json.loads(self.request.body or '{}')))
        form.validate()
        if form.errors:
            self.response.set_status(400)
            self.response.write(json.dumps(form.errors))
        else:
            try:
                User.get_by_auth_password(form.email.data, form.password.data)
                self.session['user'] = form.email.data
                self.response.write(json.dumps({'success': "Logged in"}))
            except Exception:
                self.response.set_status(400)
                self.response.write(json.dumps({'error': "Login failed"}))


class LogoutHandler(BaseHandler):
    def get(self, _id=None):
        if 'user' in self.session:
            del self.session['user']

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'test key',
}

app = webapp2.WSGIApplication([
    ('/templates/([^/]+)', TemplateHandler),
    ('/api/users/?', UserHandler),
    ('/api/messages/?', MessageHandler),
    ('/api/login/?', LoginHandler),
    ('/api/logout/?', LogoutHandler),
    ('/.*', MainHandler),
], config=config, debug=True)
