# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import inspect
import json

from openstack.identity import identity_service
from openstack.network.v2 import thin as thins
from openstack import transport as trans
from senlinclient.common import exc as client_exc


class Client(object):
    def __init__(self, session):
        self.session = session
        self.auth = session.authenticator

    def get_options(self, options):
        return json.loads(options)

    def transport(self, opts):
        '''Create a transport given some options.
        E.g.
        https://region-a.geo-1.identity.hpcloudsvc.com:35357/
        '''
        argument = opts.argument
        xport = trans.Transport(verify=opts.verify)
        return xport.get(argument).text

    def thin(self):
        # Authenticate should be done before this.
        request = thins.Thin()
        for obj in request.list_networks(self.session):
            print(obj['id'])

    def session(self, cls_name):
        if cls_name is None:
            raise Exception("A cls name argument must be specified")

        filtration = identity_service.IdentityService()
        return self.session.get(cls_name, service=filtration).text

    def authenticate(self, options):
        xport = trans.Transport(verify=options.verify)
        print(self.auth.authorize(xport))
        return xport

    def list(self, cls, **options):
        try:
            return cls.list(self.session, **options)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def list_short(self, cls, options=None):
        try:
            return cls.list_short(self.session, path_args=None, **options)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def create(self, cls, params):
        obj = cls.new(**params)
        try:
            return obj.create(self.session)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def get(self, cls, options=None):
        if options is None:
            options = {}
        try:
            obj = cls.new(**options)
            return obj.get(self.session)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def find(self, cls, options):
        return cls.find(self.session, options)

    def update(self, cls, options):
        obj = cls.new(**options)
        try:
            obj.update(self.session)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def delete(self, cls, options):
        obj = cls.new(**options)
        try:
            obj.delete(self.session)
        except Exception as ex:
            client_exc.parse_exception(ex)

    def head(self, cls, options):
        kwargs = self.get_options(options)
        obj = cls.new(**kwargs)
        obj.head(self.session)
        return obj

    def action(self, cls, options):
        def filter_args(method, params):
            expected_args = inspect.getargspec(method).args
            accepted_args = ([a for a in expected_args if a != 'self'])
            filtered_args = dict((d, params[d]) for d in accepted_args)
            return filtered_args

        def invoke_method(target, method_name, params):
            action = getattr(target, method_name)
            filtered_args = filter_args(action, params)
            reply = action(**filtered_args)
            return reply

        action = options.pop('action')
        if 'action_args' in options:
            args = options.pop('action_args')
        else:
            args = {}

        args.update(session=self.session)
        obj = cls.new(**options)
        try:
            return invoke_method(obj, action, args)
        except Exception as ex:
            client_exc.parse_exception(ex)
