# -*- coding: utf-8 -*-
#
# Copyright 2010 Facebook
# Copyright 2013 Ourbunny (modified for PhotoGrabber)
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

"""Python client library for the Facebook Platform.

This client library is designed to support the Graph API and the official
Facebook JavaScript SDK, which is the canonical way to implement
Facebook authentication. Read more about the Graph API at
http://developers.facebook.com/docs/api. You can download the Facebook
JavaScript SDK at http://github.com/facebook/connect-js/.
"""

import time
import requests
import logging
import repeater
import json

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
    """

    def __init__(self, access_token=None):
        self.access_token = access_token
        self.logger = logging.getLogger('facebook')
        self.rtt = 0 # round trip total

    def get_object(self, id, limit=500):
        """Get an entire object from the Graph API.

        Retreives an entine object by following the pages in a response.

        Args:
            id (str): The path of the object to retreive.

        Kwards:
            limit (int): The number of object to request per page (default 500)

        Returns:
            list|dict.  Context dependent

        Raises:
            GraphAPIError, ConnectionError, HTTPError, Timeout, TooManyRedirects

        >>>graph = facebook.GraphAPI(access_token)
        >>>user = graph.get_object('me')
        >>>print user['id']
        >>>photos = graph.get_object('me/photos')
        >>>for photo in photos:
        >>>    print photo['id']

        """

        # API defines max limit as 5K
        if limit > 5000: limit = 5000

        data = []

        args = {}
        args["limit"] = limit

        # first request
        self.logger.info('retieving: %s' % id)

        response = self._request(id, args) # GraphAPIError

        if response.has_key('data'):
            # response is a list
            data.extend(response['data'])

            if response.has_key('paging'):
                # iterate over pages
                while response['paging'].has_key('next'):
                    page_next = response['paging']['next']
                    response = self._follow(page_next) #GraphAPIError
                    if len(response['data']) > 0:
                        data.extend(response['data'])
                    else:
                        break
        else:
            # response is a dict
            self.logger.debug('no response key "data"')
            data = response

        self.logger.info('data size: %d' % len(data))

        return data

    @repeater.repeat
    def _follow(self, path):
        """Follow a graph API path."""

        # no need to build URL since it was given to us

        self.rtt = self.rtt+1

        try:
            r = requests.get(path)
        except requests.exceptions.SSLError as e:
            raise repeater.DoNotRepeatError(e)
        self.logger.debug('GET: %s' % r.url)
        
        response = r.json()
        self.logger.debug(json.dumps(response, indent=4))

        if response.get("error"):
            try:
                raise GraphAPIError(response["error"]["code"],
                                    response["error"]["message"])
            except GraphAPIError as e:
                if e.code == 190 or e.code == 2500:
                    # do not bother repeating if OAuthException
                    raise repeater.DoNotRepeatError(e)
                else:
                    # raise original GraphAPIError (and try again)
                    self.logger.error('GET: %s failed' % path)
                    raise

        return response

    @repeater.repeat
    def _request(self, path, args=None):
        """Fetches the given path in the Graph API."""

        if not args: args = {}
        if self.access_token:
            args["access_token"] = self.access_token

        path = ''.join(["https://graph.facebook.com/",
                        path])

        self.rtt = self.rtt+1

        try:
            r = requests.get(path, params=args)
        except requests.exceptions.SSLError as e:
            raise repeater.DoNotRepeatError(e)
        self.logger.debug('GET: %s' % r.url)
        
        response = r.json()
        self.logger.debug(json.dumps(response, indent=4))

        if response.get("error"):
            try:
                raise GraphAPIError(response["error"]["code"],
                                    response["error"]["message"])
            except GraphAPIError as e:
                if e.code == 190 or e.code == 2500:
                    # do not bother repeating if OAuthException
                    raise repeater.DoNotRepeatError(e)
                else:
                    # raise original GraphAPIError (and try again)
                    self.logger.error('GET: %s failed' % path)
                    raise

        return response

    @repeater.repeat
    def fql(self, query):
        """Execute an FQL query."""

        # see FQL documention link

        path = 'https://api.facebook.com/method/fql.query?'
        args = { "format":"json", "query" : query, "access_token" : self.access_token, }

        self.rtt = self.rtt+1

        try:
            r = requests.get(path, params=args)
        except requests.exceptions.SSLError as e:
            raise repeater.DoNotRepeatError(e)
        self.logger.debug('GET: %s' % r.url)
        
        response = r.json()
        self.logger.debug(json.dumps(response, indent=4))

        if type(response) is dict and "error_code" in response:
            # add do not repeate error
            self.logger.error('GET: %s failed' % path)
            raise GraphAPIError(response["error_code"],
                                response["error_msg"])

        return response

    def get_stats(self):
        """Returns the number of HTTP requests performed by GraphAPI."""
        return self.rtt

    def reset_stats(self):
        """Reset the number of HTTP requests performed by GraphAPI."""
        self.rtt = 0


class GraphAPIError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code

def request_token():
    """Prompt the user to login to facebook and obtain an OAuth token."""

    import webbrowser

    CLIENT_ID = "139730900025"
    RETURN_URL = "http://faceauth.appspot.com/"
    SCOPE = ''.join(['user_photos,',
                     'friends_photos,',
                     'user_likes'])

    url = ''.join(['https://graph.facebook.com/oauth/authorize?',
                   'client_id=%(cid)s&',
                   'redirect_uri=%(rurl)s&',
                   'scope=%(scope)s&',
                   'type=user_agent'])

    args = { "cid" : CLIENT_ID, "rurl" : RETURN_URL, "scope" : SCOPE, }

    webbrowser.open(url % args)
