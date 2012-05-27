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
import os
import json
import time
import urllib2
import shutil

# download album methods for multiprocessing

def save_album(album, path):
    """Process a full album.  Save data as JSON and download photos.

    album: full album data
    path: directory to save to albums
    """

    logger = logging.getLogger('save_album')

    # recursively make path
    path = os.path.join(path, album['name'])
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

        # save photos
        max_retries = 10
        retries = 0

        pic_path = os.path.join(path, photo['path'])

        # if os.path.isfile(filename):

        picout = open(pic_path, 'wb')
        handler = urllib2.Request(photo['src_big'])
        retry = True

        while retry:
            try:
                logger.info('downloading:%s' % photo['src_big'])
                data = urllib2.urlopen(handler)
                retry = False

                # save file
                picout.write(data.read())
                picout.close()
                created_time = time.strptime(photo['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
                photo['created_time_int'] = int(time.mktime(created_time))
                os.utime(pic_path, (photo['created_time_int'],) * 2)
            except Exception, e:
                if retries < max_retries:
                    retries += 1
                    logger.info('retrying download %s' % photo['src_big'])
                    # sleep longer and longer between retries
                    time.sleep(retries * 2)
                else:
                    # skip on 404 error
                    logger.info('Could not download %s' % photo['src_big'])
                    picout.close()
                    os.remove(pic_path)
                    retry = False

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
        # shutil.copy(os.path.join('dep', 'viewer.html'), htmlfilename)
    except Exception, e:
        logger.info('Saving JSON Failed: %s', filename)

    return
