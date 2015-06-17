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
from webapp2_extras.appengine import auth
from webapp2_extras import sessions

from wtforms.form import Form
from wtforms import fields
from wtforms import validators


class UserForm(Form):
    full_name = fields.StringField(u'Full Name', validators=[validators.input_required()])
    email = fields.StringField(u'Email', validators=[validators.input_required(), validators.Email()])
    password = fields.PasswordField(u'Password', validators=[validators.input_required()])


class LoginForm(Form):
    email = fields.StringField(u'Email', validators=[validators.input_required(), validators.Email()])
    password = fields.PasswordField(u'Password', validators=[validators.input_required()])


class AuthMixin(object):

    def get_auth(self):
        user, token = self.request.get('email'), self.request.get('token')
        if user and token:
            print User.validate_token(token, 'test', user)
            return User.get_by_auth_token(user, token)[0]


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



JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(BaseHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({'user': self.session.get('user', ''), 'token': self.session.get('token', '')}))


class TemplateHandler(BaseHandler):
    def get(self, template_name):
        template = JINJA_ENVIRONMENT.get_template('templates/%s' % template_name)
        self.response.write(template.render())


class UserHandler(BaseHandler, AuthMixin):
    def get(self, _id=None):
        user = self.get_auth()
        if user:
            pass
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
                user = User.get_by_auth_password(form.email.data, form.password.data)
                token = User.create_auth_token(form.email.data)
                self.session['user'] = form.email.data
                self.session['token'] = token
                self.response.write(json.dumps({'token': token}))
            except Exception, e:
                self.response.set_status(400)
                self.response.write(json.dumps({'error': "Login failed"}))


class LogoutHandler(BaseHandler, AuthMixin):
    def get(self, _id=None):
        User.delete_auth_token(self.request.get('email'), self.request.get('token'))

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'test key',
}

app = webapp2.WSGIApplication([
    ('/templates/([^/]+)', TemplateHandler),
    ('/api/users/?', UserHandler),
    ('/api/login/?', LoginHandler),
    ('/api/logout/?', LogoutHandler),
    ('/.*', MainHandler),
], config=config, debug=True)
