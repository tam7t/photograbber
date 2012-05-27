#!/usr/bin/env python
#
# Copyright (C) 2012  Ourbunny
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

class Helper(object):
    """Helper functions for retrieving Facebook data.

    Example usage:
        import facebook
        import helpers

        graph = facebook.GraphAPI(access_token)
        helper = helpers.Helper(graph)
        helper.get_friends(id)
        helper.get_subscriptions(id)
        helper.get_pages(id)
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
            except Exception,e:
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
        return self.graph.get_object('%s/friends' % id, 5000)

    def get_subscriptions(self, id):
        return self.graph.get_object('%s/subscribedto' % id, 5000)

    def get_pages(self, id):
        return self.graph.get_object('%s/likes' % id, 5000)

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

        # get comments
        if comments and 'comments' in album:
            if len(album['comments']) >= 25:
                album['comments'] = self.graph.get_object('%s/comments' % album['id'])

        # get album photos
        album['photos'] = self.graph.get_object('%s/photos' % album['id'])

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
        if type(album) is not dict:
            import pdb;pdb.set_trace()
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
        return data

    def get_tagged(self, id, comments=False, full=True):
        """Get all photos where argument id is tagged.

        id: the object_id of target
        comments: set to True to retrieve all comments
        full: get all photos from all album the user is tagged in
        """

        self.logger.info('get_tagged: %s' % id)

        unsorted = self.graph.get_object('%s/photos' % id)
        unsorted_ids = [x['id'] for x in unsorted]
        album_ids = self.find_album_ids(unsorted_ids)

        data = []

        self.logger.info('%d photos in %d albums' % (len(unsorted_ids), len(album_ids)))

        # TODO: this could be done in parallel
        for album_id in album_ids:
            album = self.get_album(album_id, comments)
            # remove id's from unsorted that are in the album
            photo_ids = [x['id'] for x in album['photos']]
            unsorted = [x for x in unsorted if x['id'] not in photo_ids]
            if not full:
                # limit album to only those in unsorted, even though we now
                # have information on them all... graph API sucks
                photos = [x for x in unsorted if x['id'] in photo_ids]
                album['photos'] = photos
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
