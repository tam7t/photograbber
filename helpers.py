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

import logging
import collections

class Helper(object):
    """Helper functions for retrieving Facebook data.

    Example usage:
        import facebook
        import helpers

        graph = facebook.GraphAPI(access_token)
        helper = helpers.Helper(graph)
        helper.get_friends(id)
        helper.get_subscriptions(id)
        helper.get_likes(id)
        helper.get_albums(id)
        helper.get_tagged(id)
        helper.get_tagged_albums(id)

    The id field in all cases is the id of the target for backup.
    """

    def __init__(self, graph=None):
        self.graph = graph
        self.logger = logging.getLogger('helper')

    def find_album_ids(self, picture_ids):
        """Find the albums that contains pictures.

        The picture_id arguement must be a list of photo object_id's.

        Returns a list of album object_id's.  If permissions for the album do
        not allow for album information to be retrieved then it is omitted from
        the list.
        """

        q = ''.join(['SELECT object_id, aid FROM album WHERE aid ',
                     'IN (SELECT aid FROM photo WHERE object_id IN (%s))'])

        ids = []

        # split query into 25 pictures at a time
        for i in range(len(picture_ids) / 25 + 1):
            pids = ','.join(picture_ids[i * 25:(i+1) * 25])
            new_ids = self.graph.fql(q % pids)
            try:
                new_ids = [x['object_id'] for x in new_ids]
            except Exception as e:
                self.logger.error('no album access')
                self.logger.error('%s' % e)
                bad_query = q % pids
                self.logger.error('query: %s' % bad_query)
                new_ids = []

            ids = list(set(ids+new_ids))

        return ids

    # The following methods return a list of object id <> friend
    # [ {'id':<id>, 'name':<name>}, ... ]

    def get_me(self):
        return self.graph.get_object('me')

    def get_info(self, id):
        return self.graph.get_object('%s' % id)

    def get_friends(self, id):
        data = self.graph.get_object('%s/friends' % id, 5000)
        return sorted(data, key=lambda k:k['name'].lower())

    def get_subscriptions(self, id):
        data = self.graph.get_object('%s/subscribedto' % id, 5000)
        return sorted(data, key=lambda k:k['name'].lower())

    def get_likes(self, id):
        data = self.graph.get_object('%s/likes' % id, 5000)
        return sorted(data, key=lambda k:k['name'].lower())

    # return the list of album information that id has uploaded

    def get_album_list(self, id):
        return self.graph.get_object('%s/albums' % id)

    # The following methods return a list of albums & photos
    # returns [{album_1}, ..., {album_n} ]
    # where album_n = {'id':<id>, 'comments':[<>], 'photos':[<>], ... }

    # note: there is a potential for optimization of comments
    #   only download comments if
    #       1) we want comments
    #       2) if comments already exists
    #       3) follow comment paging, instead of re-getting all


    def _fill_album(self, album, comments):
        """Takes an already loaded album and fills out the photos and
        comments"""

        # album must be dictionary, with 'photos'

        # get comments
        if comments and 'comments' in album:
            if len(album['comments']) >= 25:
                album['comments'] = self.graph.get_object('%s/comments' % album['id'])

        # get album photos
        album['photos'] = self.graph.get_object('%s/photos' % album['id'], limit=50)

        if len(album['photos']) == 0:
            self.logger.error('album had zero photos: %s' % album['id'])
            return None

        for photo in album['photos']:
            # get picture comments
            if comments and 'comments' in photo:
                n_before = len(photo['comments']['data'])
                # using examples from: georgehtakei/photos
                # the default number of comments to inculde in a photo from
                # /photos or /<album>/photos is 25
                # this applies to likes also
                if n_before >= 25:
                    photo['comments'] = self.graph.get_object('%s/comments' % photo['id'])
                    n_after = len(photo['comments'])
                    if n_before != n_after:
                        self.logger.info('found more comments:' + str(n_before) + ' to ' + str(n_after))
        return album

    def get_album(self, id, comments=False):
        """Get a single album"""

        self.logger.info('begin get_album: %s' % id)

        # handle special case:
        # create empty album if there are not permissions to view album info
        # but can see photo from tagged
        if id == '0':
            album= {}
            album['id'] = '0'
            album['name'] = 'Unknown'
            album['comments'] = []
            album['photos'] = []
            return album

        album = self.graph.get_object('%s' % id)
        return self._fill_album(album, comments)

    def get_albums(self, id, comments=False):
        """Get all albums uploaded by id"""

        self.logger.info('get_albums: %s' % id)

        data = self.graph.get_object('%s/albums' % id)
        self.logger.info('albums: %d' % len(data))

        for album in data:
            album = self._fill_album(album, comments)
     
        # remove empty albums
        data = [album for album in data if album is not None]
        data = [album for album in data if len(album['photos']) > 0]
        return data

    def get_tagged(self, id, comments=False, full=True):
        """Get all photos where argument id is tagged.

        id: the object_id of target
        comments: set to True to retrieve all comments
        full: get all photos from all album the user is tagged in
        """

        self.logger.info('get_tagged: %s' % id)

        unsorted = self.graph.get_object('%s/photos' % id)
        self.logger.info('tagged in %d photos' % len(unsorted))
        
        unsorted_ids = [x['id'] for x in unsorted]
        album_ids = self.find_album_ids(unsorted_ids)

        data = []

        self.logger.info('%d photos in %d albums' % (len(unsorted_ids), len(album_ids)))

        # TODO: this could be done in parallel
        for album_id in album_ids:
            album = self.get_album(album_id, comments)
            photo_ids = [x['id'] for x in album['photos']]
            if not full:
                # limit album to only those in unsorted, even though we now
                # have information on them all... graph API sucks
                photos = [x for x in unsorted if x['id'] in photo_ids]
                album['photos'] = photos
            # remove id's from unsorted that are in the album
            unsorted = [x for x in unsorted if x['id'] not in photo_ids]
            data.append(album)

        # anything not claimed under album_ids will fall into fake album
        if len(unsorted) > 0:
            empty_album = self.get_album('0', comments)
            empty_album['photos'] = unsorted

            for photo in empty_album['photos']:
                # get picture comments
                if comments and 'comments' in photo:
                    photo['comments'] = self.graph.get_object('%s/comments' % photo['id'])

            data.append(empty_album)

        # remove empty albums
        data = [album for album in data if album is not None]

        return data

import threading
import repeater
import requests
import Queue
import os
import time
import re
import shutil
import json

class DownloaderThread(threading.Thread):
    def __init__(self, q):
        """make many of these threads.
        
        pulls tuples (photo, album_path) from queue to download"""
        
        threading.Thread.__init__(self)
        self.daemon=True
        self.q = q
        self.logger = logging.getLogger('DownloadThread')

    @repeater.repeat
    def _download(self, web_path):
        r = requests.get(web_path)
        return r.content
    
    def run(self):
        while True:
            photo, path = self.q.get()

            try:
                save_path = os.path.join(path, photo['path'])
                web_path = photo['src_big']

                picout = open(save_path, 'wb')
                self.logger.info('downloading:%s' % web_path)
                try:
                    picout.write(self._download(web_path))
                finally:
                    picout.close()

                # correct file time
                created_time = time.strptime(photo['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
                time_int = int(time.mktime(created_time))
                os.utime(save_path, (time_int,) * 2)
            except Exception as e:
                self.logger.error(e)

            self.q.task_done()

class ProcessThread(threading.Thread):
    def __init__(self, helper, config):
        threading.Thread.__init__(self)
        self.helper = helper
        self.config = config
        self.logger = logging.getLogger('ProcessThread')
        self.q = Queue.Queue()
        self.msg = "Downloading..."
        self.pics = 0
        self.total = 0

    def _processAlbum(self, album, path, comments):
        # recursively make path
        # http://serverfault.com/questions/242110/which-common-charecters-are-illegal-in-unix-and-windows-filesystems
        #
        # NULL and / are not valid on EXT3
        # < > : " / \ | ? * are not valid Windows
        # prohibited characters in order:
        #   * " : < > ? \ / , NULL
        #
        #   '\*|"|:|<|>|\?|\\|/|,|'
        # add . for ... case
        REPLACE_RE = re.compile(r'\*|"|:|<|>|\?|\\|/|,|\.')
        folder = unicode(album['folder_name'])
        folder = REPLACE_RE.sub('_', folder)
        path = os.path.join(path, folder)
        if not os.path.isdir(path):
            os.makedirs(path) # recursive makedir

        # save files
        for photo in album['photos']:
            # set 'src_big' to largest photo size
            width = -1
            for image in photo['images']:
                if image['width'] > width:
                    photo['src_big'] = image['source']
                    width = image['width']

            # filename of photo
            photo['path'] = '%s' % photo['src_big'].split('/')[-1]

            # TODO: add photo to queue
            self.q.put( (photo,path) )

        # exit funcion if no need to save metadata
        if not comments:
            return

        # save JSON file
        ts = time.strftime("%y-%m-%d_%H-%M-%S")

        filename = os.path.join(path, 'pg_%s.json' % ts)
        alfilename = os.path.join(path, 'album.json')
        htmlfilename = os.path.join(path, 'viewer.html')
        try:
            db_file = open(filename, "w")
            db_file.write("var al = ");
            json.dump(album, db_file)
            db_file.write(";\n")
            db_file.close()
            shutil.copy(filename, alfilename)
            shutil.copy(os.path.join('dep', 'viewer.html'), htmlfilename)
        except Exception as e:
            self.logger.error(e)

    def run(self):
        """Collect all necessary information and download all files"""
    
        for i in range(50):
            t=DownloaderThread(self.q)
            t.start()

        savedir = self.config['dir']
        targets = self.config['targets']
        u = self.config['u']
        t = self.config['t']
        c = self.config['c']
        a = self.config['a']

        self.logger.info("%s" % self.config)

        for target in targets:
            target_info = self.helper.get_info(target)
            data = []
            u_data = []

            # get user uploaded photos
            if u:
                self.msg = 'Retrieving %s\'s album data...' % target_info['name']
                u_data = self.helper.get_albums(target, comments=c)

            t_data = []
            # get tagged
            if t:
                self.msg = 'Retrieving %s\'s tagged photo data...' % target_info['name']
                t_data = self.helper.get_tagged(target, comments=c, full=a)

            if u and t:
                # list of user ids
                u_ids = [album['id'] for album in u_data]
                # remove tagged albums if part of it is a user album
                t_data = [album for album in t_data if album['id'] not in u_ids]

            data.extend(u_data)
            data.extend(t_data)
            
            # find duplicate album names
            names = [album['name'] for album in data]
            duplicate_names = [name for name, count in collections.Counter(names).items() if count > 1]
            for album in data:
                if album['name'] in duplicate_names:
                    album['folder_name'] = '%s - %s' % (album['name'], album['id'])
                else:
                    album['folder_name'] = album['name']

            self.total = 0
            for album in data:
                self.total = self.total + len(album['photos'])

            self.msg = 'Downloading %d photos...' % self.total

            for album in data:
                path = os.path.join(savedir,unicode(target_info['name']))
                self._processAlbum(album, path, c)

            self.logger.info('Waiting for childeren to finish')
            
            self.q.join()

            self.logger.info('Child processes completed')
            self.logger.info('albums: %s' % len(data))
            self.logger.info('pics: %s' % self.total)

            self.msg = '%d photos downloaded!' % self.total
    
    def status(self):
        return self.msg
        
    def progress(self):
        return (self.total - self.q.qsize(), self.total)