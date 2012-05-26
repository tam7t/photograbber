#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Modified for photograbber by Tommy Murphy, ourbunny.com

"""Python client library for the Facebook Platform.

This client library is designed to support the Graph API and the official
Facebook JavaScript SDK, which is the canonical way to implement
Facebook authentication. Read more about the Graph API at
http://developers.facebook.com/docs/api. You can download the Facebook
JavaScript SDK at http://github.com/facebook/connect-js/.
"""

import cgi
import hashlib
import time
import urllib
import logging

# Find a JSON parser
try:
    import json
    _parse_json = lambda s: json.loads(s)
except ImportError:
    try:
        import simplejson
        _parse_json = lambda s: simplejson.loads(s)
    except ImportError:
        # For Google AppEngine
        from django.utils import simplejson
        _parse_json = lambda s: simplejson.loads(s)

class GraphAPI(object):
    """A client for the Facebook Graph API.

    See http://developers.facebook.com/docs/api for complete documentation
    for the API.

    The Graph API is made up of the objects in Facebook (e.g., people, pages,
    events, photos) and the connections between them (e.g., friends,
    photo tags, and event RSVPs). This client provides access to those
    primitive types in a generic way. For example, given an OAuth access
    token, this will fetch the profile of the active user and the list
    of the user's friends:

       graph = facebook.GraphAPI(access_token)
       user = graph.get_object("me")
       friends = graph.get_connections(user["id"], "friends")

    You can see a list of all of the objects and connections supported
    by the API at http://developers.facebook.com/docs/reference/api/.

    You can obtain an access token via OAuth or by using the Facebook
    JavaScript SDK. See http://developers.facebook.com/docs/authentication/
    for details.

    If you are using the JavaScript SDK, you can use the
    get_user_from_cookie() method below to get the OAuth access token
    for the active user from the cookie saved by the SDK.
    """

    def __init__(self, access_token=None):
        self.access_token = access_token
        self.logger = logging.getLogger('facebook')
        self.rtt = 0

    def get_object(self, id, limit=50):
        """Get an entine object from the Graph API by paging over the requested
        object until the entire object is retrieved.

            graph = facebook.GraphAPI(access_token)
            user = graph.get_object('me')
            print user['id']

        id: path to the object to retrieve
        limit: number of objects to retrieve in each page
        """

        data = []
        has_more = True

        args = {}
        args["limit"] = limit
        args["offset"] = 0

        while (has_more):
            self.logger.info('retieving: %s' % id)

            response = self._request(id, args)

            # TODO: find if this 'if no' is ever executed
            if not response.has_key('data'):
                return response

            if len(response['data']) < limit:
                data.extend(response['data'])
                self.logger.info('elements: %d' % len(data))
                has_more = False
            else:
                data.extend(response['data'])
                args['offset'] = len(data)

        return data


    def _request_once(self, path, args=None):
        """Fetches the given path in the Graph API."""

        if not args: args = {}
        if self.access_token:
            args["access_token"] = self.access_token

        path = ''.join(["https://graph.facebook.com/",
                        path,
                        "?",
                        urllib.urlencode(args)])

        self.logger.debug('GET: %s' % path)
        file = urllib.urlopen(path)

        self.rtt = self.rtt+1

        try:
            response = _parse_json(file.read())
            self.logger.debug(json.dumps(response, indent=4))
        finally:
            file.close()
        if response.get("error"):
            raise GraphAPIError(response["error"]["type"],
                                response["error"]["message"])
        return response

    def _request(self, path, args=None, n=10, standoff=1.5):
        """Execute a Graph request.  Repeats on failure.

        path: properly formatted path in the Graph API
        args: list of extra arguments, 'limit' and 'offset'
        n: retry the call <n> times before raising an error
        standoff: multiplier increment for each standoff
        """

        retries = 0
        while True:
            try:
                return self._request_once(path, args)
            except Exception, e:
                self.logger.error('path request failed: %s' % path)
                self.logger.error('args = %s' % args)
                if retries < n:
                    retries += 1
                    time.sleep(retries * standoff)
                else:
                    raise

    def _fql_once(self, query):
        """Execute an FQL query once.

        query: properly formatted FQL query to execute
        """

        query = urllib.quote(query)
        path = ''.join(['https://api.facebook.com/method/fql.query?',
                        'format=json&',
                        'query=%(q)s&',
                        'access_token=%(at)s'])
        args = { "q" : query, "at" : self.access_token, }
        path = path % args

        self.logger.debug('GET: %s' % path)
        file = urllib.urlopen(path)

        self.rtt = self.rtt+1

        try:
            response = _parse_json(file.read())
            self.logger.debug(json.dumps(response, indent=4))
            if type(response) is dict and "error_code" in response:
                raise GraphAPIError(response["error_code"],
                                    response["error_msg"])
        except Exception, e:
            # pass exception up!
            raise e
        finally:
            file.close()
        return response

    def fql(self, query, n=10, standoff=1.5):
        """Execute an FQL query.  Repeats on failure.

        query: properly formatted FQL query to execute
        n: retry the call <n> times before raising an error
        standoff: multiplier increment for each standoff
        """

        retries = 0
        while True:
            try:
                return self._fql_once(query)
            except Exception, e:
                self.logger.error('query failed: %s' % query)
                if retries < n:
                    retries += 1
                    time.sleep(retries * standoff)
                else:
                    raise

    def get_stats(self):
        return self.rtt

    def reset_stats(self):
        self.rtt = 0

class GraphAPIError(Exception):
    def __init__(self, type, message):
        Exception.__init__(self, message)
        self.type = type

### photograbber Additions ###

import webbrowser

CLIENT_ID = "139730900025"
RETURN_URL = "http://faceauth.appspot.com/"
SCOPE = ''.join(['user_photo_video_tags,',
                 'friends_photo_video_tags,',
                 'user_photos,',
                 'friends_photos,',
                 'user_likes'])

def request_token():
    """Prompt the user to login to facebook and obtain an OAuth token."""

    url = ''.join(['https://graph.facebook.com/oauth/authorize?',
                   'client_id=%(cid)s&',
                   'redirect_uri=%(rurl)s&',
                   'scope=%(scope)s&',
                   'type=user_agent'])

    args = { "cid" : CLIENT_ID, "rurl" : RETURN_URL, "scope" : SCOPE, }

    webbrowser.open(url % args)

