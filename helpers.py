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

    def find_album_id(self, picture_id):
        """Find the album that contains a picture.

        The picture_id arguement must be the object_id of a photo.

        Returns the object_id of the album.
        """

        q = ''.join(['SELECT object_id, aid FROM album WHERE aid ',
                     'IN (SELECT aid FROM photo WHERE object_id=%s)'])
        data = self.graph.fql(q % picture_id)

        # TODO: verify data response when photo_id does not exist
        if len(data) == 1:
            return data[0]['object_id']
        else:
            self.logger.error('No object_id found (photo): %s' % picture_id)
            self.logger.error('Response: %s' % data)
            return '0'

    def find_album_photos(self, album_id):
        """Find all photos in an album.

        The album_id arguement must be the object_id of an album.

        Returns a list of photos in the form:
        [{'object_id':'<object_id>', 'pid':'<pid>'}, ...]
        """

        q = ''.join(['SELECT object_id, pid FROM photo WHERE aid ',
                     'IN (SELECT aid FROM album WHERE object_id=%s'])
        data = self.query(q % album_id)

        # TODO: verify data response when album_id does not exist
        if len(data) == 0:
            self.logger.error('No object_id found (album): %s' % album_id)
            self.logger.error('Response: %s' % data)
        return data

    # The following methods return a list of object id <> friend
    # { '<object id>' : 'Friend Name', ...}

    def get_friends(self, id):
        return self.graph.get_object('%s/friends' % id, 5000)

    def get_subscriptions(self, id):
        return self.graph.get_object('%s/subscribedto' % id, 5000)

    def get_pages(self, id):
        return self.graph.get_object('%s/likes' % id, 5000)

    # The following methods return a list of albums & photos
    # { '<album object id>': {'<picture id>':<data>, ...}, ...}

    def get_albums(self, id):
        """Get all albums uploaded by id"""
        data = self.graph.get_object('%s/albums' % id, 100)
        data['comments'] = self.graph.get_object('%s/comments' % data['id'])

        # does not follow comments and likes paging
        return data

    def get_tagged(self, id):
        """Get all photos where argument id is tagged"""

        unsorted = self.graph.get_object('%s/photos' % id, 5000)
        # must follow comments and likes paging...
        data = {}
        while len(unsorted) > 0:
            self.logger.info('len(unsorted) = %d' % len(unsorted))

            aid = '%s' % find_album(unsorted[0]['id'])
            # get album info
            data[aid] = self.graph.get_object('%s' % aid, 100)
            data[aid]['comments'] = self.graph.get_object('%s/comments' % aid, 100)
            # get list of photos
            photos = self.graph.get_object('%s/photos' % aid, 100)
            # get list of photo id's
            photo_ids = [x['id'] for x in photos]
            # only add photos from unsorted to list
            data[aid]['photos'] = [x for x in unsorted if x['id'] in photo_ids]
            # get each photo's comments
            for photo in data[aid]['photos']:
                photo['comments'] = self.graph.get_object('%s/comments' % photo['id'])
            # remove  from unsorted
            unsorted = [x for x in unsorted if x['id'] not in photo_ids]

        return data

    def get_tagged_albums(self, id):
        """Get all photos from all albums where argument id is tagged"""

        unsorted = self.graph.get_object('%s/photos' % id, 5000)
        # must follow comments and likes paging...
        data = {}
        while len(unsorted) > 0:
            self.logger.info('len(unsorted) = %d' % len(unsorted))

            aid = '%s' % find_album(unsorted[0]['id'])
            # get album info
            data[aid] = self.graph.get_object('%s' % aid, 100)
            data[aid]['comments'] = self.graph.get_object('%s/comments' % aid, 100)
            # get list of photos
            data[aid]['photos'] = self.graph.get_object('%s/photos' % aid, 100)
            # get each photo's comments
            for photo in data[aid]['photos']:
                photo['comments'] = self.graph.get_object('%s/comments' % photo['id'])
            # get list of photo id's
            photo_ids = [x['id'] for x in data[aid]['photos']]
            # remove  from unsorted
            unsorted = [x for x in unsorted if x['id'] not in photo_ids]

        return data

