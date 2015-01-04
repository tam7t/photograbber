# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Ourbunny
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging
import Queue
import repeater
import requests
import threading

log = logging.getLogger('pg.%s' % __name__)

class GraphBuilder(object):
    def __init__(self, access_token=None):
        self.access_token = access_token

    def set_token(self, access_token):
        self.access_token = access_token

    def get_object(self, path, limit=100):
        # API defines max limit as 5K
        if limit > 5000: limit = 5000

        args = {}
        #if limit > 0:
        #   args["limit"] = limit
        args["access_token"] = self.access_token

        path = ''.join(["https://graph.facebook.com/v2.2/",
                        path])

        return path, args

    def fql(self, query):
        # see FQL documention link

        path = 'https://api.facebook.com/method/fql.query?'
        args = { "format":"json", "query" : query,
                 "access_token" : self.access_token, }
                 
        return path, args

    def parse(self, response, url):
        if type(response) is dict and "error_code" in response:
            log.error('GET: %s failed' % url)
            raise GraphAPIError(response["error_code"],
                                response["error_msg"],
                                url)

        if type(response) is dict and "error" in response:
            log.error('GET: %s failed' % url)
            raise GraphAPIError(response["error"]["code"],
                                response["error"]["message"],
                                url)

        return response


class GraphAPIError(Exception):
    """Error raised through Facebook API."""

    def __init__(self, code, message, url):
        Exception.__init__(self, message)
        self.code = code
        self.url = url


class GraphRequestHandler(threading.Thread):
    def __init__(self, request_queue, response_queue, graph_builder):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.graph_builder = graph_builder

    @repeater.repeat
    def _get(self, request):
        if 'path' in request:
            path, args = self.graph_builder.get_object(request['path'])
        elif 'query' in request:
            path, args = self.graph_builder.fql(request['query'])
        elif 'url' in request:
            path, args = request['url'], []
        else:
            raise repeater.DoNotRepeatError(TypeError('Malformed request'))

        try:
            r = requests.get(path, params=args)
        except requests.exceptions.SSLError as e:
            raise repeater.DoNotRepeatError(e)

        log.debug('GET: %s' % r.url)
        response = r.json()
        #log.debug(json.dumps(response, indent=4))

        try:
            retVal = self.graph_builder.parse(response, r.url)
        except GraphAPIError as e:
            # https://developers.facebook.com/docs/reference/api/errors/
            # do not try on OAuth errors
            if e.code is 190:
                raise repeater.DoNotRepeatError(e)
            # API Too Many Calls (server side throttling)
            # API User Too Many Calls
            if e.code is 4 or e.code is 17:
                raise repeater.PauseRepeatError(e, 60)
            raise e
        return retVal

    def run(self):
        while True:
            request = self.request_queue.get()

            #process request
            more = True
            while more:
                try:
                    response = self._get(request)
                except Exception as e:
                    request['error'] = e # notify of error!
                    request['more'] = False
                    self.response_queue.put(request)
                    break

                if 'data' in response:
                    request['response'] = response['data']
                else:
                    request['response'] = response

                # is there an option to page over responses
                more = False
                if 'paging' in response:
                    if len(response['data']) > 0:
                        if 'next' in response['paging']:
                            next_request = request.copy()
                            next_request.pop('response', None)
                            next_request.pop('path', None)
                            next_request.pop('query', None)
                            next_request['url'] = response['paging']['next']
                            more = True

                request['more'] = more
                self.response_queue.put(request)
                if more:
                    request = next_request

            self.request_queue.task_done()


class GraphAPI(threading.Thread):
    def __init__(self, access_token):
        threading.Thread.__init__(self)
        self.daemon = True

        self.graph_builder = GraphBuilder()
        self.set_token(access_token)

        self.id = 0
        self.active = []
        self.activeLock = threading.Lock()

        self.data = {}
        self.errors ={}
        self.dataLock = threading.Lock()

        self.request_queue = Queue.Queue()
        self.response_queue = Queue.Queue()
        self.threads = []

    def run(self):
        # create my worker threads
        for n in range(10):
            t = GraphRequestHandler(self.request_queue, self.response_queue,
                                    self.graph_builder)
            self.threads.append(t)
            t.start()

        # process responses
        while True:
            response = self.response_queue.get()

            # save response in data dictionary
            self.dataLock.acquire()
            if 'response' in response:
                data = response['response']
                if response['id'] in self.data:
                    try:
                        self.data[response['id']].extend(data)
                    except Exception as e:
                        import pdb; pdb.set_trace()
                else:
                    self.data[response['id']] = data
            elif 'error' in response:
                self.errors[response['id']] = response['error']
            self.dataLock.release()

            # processing on 'id' is complete
            if not response['more']:
                self.activeLock.acquire()
                self.active.remove(response['id'])
                self.activeLock.release()

            self.response_queue.task_done()

    def set_token(self, access_token):
        # clear all logs of any tokens, for security
        if access_token is not None:
            format = logging.root.handlers[0].formatter._fmt
            formatter = FacebookFormatter(format, access_token)
            logging.root.handlers[0].setFormatter(formatter)
    
        self.graph_builder.set_token(access_token)

    def make_request(self, request):
        """ request should only have one of path, query, url
                request = {
                            'id': <id>,
                            'path': <path>,
                            'query': <query>,
                            'url': <url>,
                            --- after served ---
                            'response': <response dict|list>,
                            'more': <True|False>, internal use, says whether response is last one or if there are 'more'
                            'error': <response error object>,
                          }
        """
        self.activeLock.acquire()
        self.id += 1
        request['id'] = self.id
        self.active.append(request['id'])
        self.activeLock.release()
        self.request_queue.put(request)
        return request['id']

    def make_requests(self, requests):
        self.activeLock.acquire()
        rids = []
        for request in requests:
            self.id += 1
            request['id'] = self.id
            self.active.append(request['id'])
            self.request_queue.put(request)
            rids.append(request['id'])
        self.activeLock.release()
        return rids

    def request_active(self, id):
        # answers the question: is the request done?
        self.activeLock.acquire()
        retVal = id in self.active
        self.activeLock.release()
        return retVal
    
    def requests_active(self, ids):
        self.activeLock.acquire()
        retVal = False
        if len(list(set(ids) & set(self.active))) > 0:
            retVal = True
        self.activeLock.release()
        return retVal
        
    def has_data(self, id):
        self.dataLock.acquire()
        # data can mean data or an error
        retVal = id in self.data or id in self.errors
        self.dataLock.release()
        return retVal

    def get_data(self, id):
        # returns available data, does not block
        # will return all data before raising an error
        retVal = retErr = None

        self.dataLock.acquire()
        if id in self.data:
            retVal = self.data.pop(id, None)
        elif id in self.errors:
            retErr = self.errors.pop(id, None)
        self.dataLock.release()
        
        if retErr is not None:
            raise retErr
        else:
            return retVal

class FacebookFormatter(logging.Formatter):
    def __init__(self, format, token):
        logging.Formatter.__init__(self, format)
        self.token = token

    def format(self, record):
        msg = logging.Formatter.format(self, record)
        return msg.replace(self.token, "<TOKEN>")
            
def request_token():
    """Prompt the user to login to facebook using their default web browser to
       obtain an OAuth token."""

    import webbrowser

    CLIENT_ID = "139730900025"
    RETURN_URL = "https://faceauth.appspot.com/?version=2200"
    SCOPE = ''.join(['user_photos,',
                     'user_likes,',])

    url = ''.join(['https://www.facebook.com/v2.2/dialog/oauth?',
                   'client_id=%(cid)s&',
                   'redirect_uri=%(rurl)s&',
                   'scope=%(scope)s&',
                   'type=user_agent'])

    args = { "cid" : CLIENT_ID, "rurl" : RETURN_URL, "scope" : SCOPE, }
    
    log.info(url % args)

    webbrowser.open(url % args)