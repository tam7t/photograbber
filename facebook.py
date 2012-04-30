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
# Modified for Photograbber by Tommy Murphy, ourbunny.com

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

    def get_object(self, id, limit=50):
        """Fetchs the given object from the graph."""

        data = []
        has_more = True

        args = {}
        args["limit"] = limit
        args["offset"] = 0

        while (has_more):
            response = self.request(id, args)
            if not response.has_key('data'):
                return response
            if len(response['data']) == 0:
                has_more = False
            else:
                data.extend(response['data'])
                args['offset'] = len(data)

        return data

    def get_objects(self, ids, **args):
        """Fetchs all of the given object from the graph.

        We return a map from ID to object. If any of the IDs are invalid,
        we raise an exception.
        """
        args["ids"] = ",".join(ids)
        return self.request("", args)

    def request(self, path, args=None):
        """Fetches the given path in the Graph API.

        We translate args to a valid query string.
        """
        if not args: args = {}
        if self.access_token:
            args["access_token"] = self.access_token

        file = urllib.urlopen("https://graph.facebook.com/" + path + "?" +
                              urllib.urlencode(args))

        try:
            response = _parse_json(file.read())
        finally:
            file.close()
        if response.get("error"):
            raise GraphAPIError(response["error"]["type"],
                                response["error"]["message"])
        return response

    def fql(self, query):
        """Provide a way to do FQL queries"""

        query = urllib.quote(query)
        path = ''.join(['https://api.facebook.com/method/fql.query?',
                        'format=json&',
                        'query=%(q)s&',
                        'access_token=%(at)s'])
        args = { "q" : query, "at" : self.access_token, }
        file = urllib.urlopen(path % args)
        try:
            response = _parse_json(file.read())
            if type(response) is dict and "error_code" in response:
                raise GraphAPIError(response["error_code"],
                                    response["error_msg"])
        except Exception, e:
            raise e
        finally:
            file.close()
        return response

class GraphAPIError(Exception):
    def __init__(self, type, message):
        Exception.__init__(self, message)
        self.type = type

 ### PhotoGrabber Additions ###

import webbrowser

CLIENT_ID = "139730900025" # old_id: "227fe70470173eca69e4b38b6518fbfda"
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

