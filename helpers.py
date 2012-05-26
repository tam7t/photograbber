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

        # find all tagged photos
        # feed pid's to find albums
        # pull album info
        # pull photos from albums
        # pull comments & likes

    def find_album_id(self, picture_id):
        """Find the album that contains a picture.

        The picture_id arguement must be the object_id of a photo.

        Returns the object_id of the album or '0' if the album cannot be
        retrieved.
        """

        # TODO: allow picture_id's to be a list

        q = ''.join(['SELECT object_id, aid FROM album WHERE aid ',
                     'IN (SELECT aid FROM photo WHERE object_id=%s)'])
        data = self.graph.fql(q % picture_id)

        # TODO: verify data response when photo_id does not exist
        if len(data) == 1:
            return data[0]['object_id']
        else:
            self.logger.error('%s' % q)
            self.logger.error('No object_id found (photo): %s' % picture_id)
            self.logger.error('Response: %s' % data)
            return '0'

    # The following methods return a list of object id <> friend
    # [ {'id':<id>, 'name':<name>}, ... ]

    def get_me(self):
        return self.graph.get_object('me')

    def get_friends(self, id):
        return self.graph.get_object('%s/friends' % id, 5000)

    def get_subscriptions(self, id):
        return self.graph.get_object('%s/subscribedto' % id, 5000)

    def get_pages(self, id):
        return self.graph.get_object('%s/likes' % id, 5000)

    # return the list of album information that id has uploaded

    def get_album_list(self, id):
        return self.graph.get_object('%s/albums' % id, 100)

    # The following methods return a list of albums & photos
    # returns [{album_1}, ..., {album_n} ]
    # where album_n = {'id':<id>, 'comments':[<>], 'photos':[<>], ... }

    # note: there is a potential for optimization of comments
    #   only download comments if
    #       1) we want comments
    #       2) if comments already exists
    #       3) follow comment paging, instead of re-getting all

    def get_album(self, id, comments=False):
        """Get a single album"""

        self.logger.info('begin get_album: %s' % id)

        # handle special case, when PG does not have permissions to get info on
        # the album, but can see the photo
        if id == '0':
            album= {}
            album['id'] = '0'
            album['name'] = 'Unknown'
            album['comments'] = []
            album['photos'] = []
            return album
        elif id ==  0:
            import pdb;pdb.set_trace()

        try:
            album = self.graph.get_object('%s' % id)
        except Exception, e:
            import pdb;pdb.set_trace()

        # get comments
        if comments and 'comments' in album:
            album['comments'] = self.graph.get_object('%s/comments' % album['id'])
        # get album photos
        album['photos'] = self.graph.get_object('%s/photos' % album['id'],500)
        for photo in album['photos']:
            # get picture comments
            if comments and 'comments' in photo:
                photo['comments'] = self.graph.get_object('%s/comments' % photo['id'])
        return album

    def get_albums(self, id, comments=False):
        """Get all albums uploaded by id"""

        self.logger.info('begin get_albums: %s' % id)

        data = self.graph.get_object('%s/albums' % id, 100)
        for album in data:
            album = self.get_album(album['id'], comments)
        return data

    def get_tagged(self, id, comments=False, full=True):
        """Get all photos where argument id is tagged.

        id: the object_id of target
        full: get all photos from all album the user is tagged in
        """

        self.logger.info('begin get_tagged: %s' % id)

        unsorted = self.graph.get_object('%s/photos' % id, 5000)
        unsorted_ids = [x['id'] for x in unsorted]

        # holder album for special case
        empty_album = self.get_album(0, comments)
        empty_album_n = 0

        aids = []

        data = []
        while len(unsorted) > 0:
            self.logger.info('len(unsorted) = %d' % len(unsorted))

            aid = '%s' % self.find_album_id(unsorted[0]['id'])

            try:
                temp = aids.index(aid)
                self.logger.error('%s already in aids' % aid)
            except Exception,e:
                aids.append(aid)

            album = self.get_album(aid, comments)

            # aid = '0' special case:
            #   album will not have any 'photos' so we must force it
            if aid == '0':
                empty_album_n = empty_album_n + 1
                if empty_album_n == 0:
                    data.append(empty_album)
                empty_album['photos'].append(unsorted[0])
                unsorted.remove(unsorted[0])
            else:
                # remove id's from unsorted that are in the album
                photo_ids = [x['id'] for x in album['photos']]
                unsorted = [x for x in unsorted if x['id'] not in photo_ids]
                # limit album to only those in unsorted
                if not full:
                    photos = [x for x in unsorted if x['id'] in photo_ids]
                    album['photos'] = photos
                data.append(album)

        return data
