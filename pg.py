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

import facebook
import helpers
import argparse
import time
import logging

def main():
    parser = argparse.ArgumentParser(description="Download Facebook photos.")
    parser.add_argument('--token', help='Specify the OAuth token used to authenticate with Facebook.')
    parser.add_argument('--list-targets', choices=('me','friends','pages','following','all'), help='Display names and object_id\'s of potential targets')
    parser.add_argument('--list-albums', nargs='+', help='List the albums uploaded by a target.  Separate the object_id\'s of targets with spaces.')
    parser.add_argument('--target', nargs='+', help='Download targets. Separate the object_id\'s of people or pages with spaces.')
    parser.add_argument('-c', action='store_true', help='Download comments. (Use with --target)')
    parser.add_argument('-a', action='store_true', help='Download full album. (Use with --target)')
    parser.add_argument('-u', action='store_true', help='Download identity\'s albums. (Use with --target)')
    parser.add_argument('-t', action='store_true', help='Download identity\'s tagged photos. (Use with --target)')
    parser.add_argument('--album', nargs='+', help='Download full albums.  Separate the object_id\'s of the albums with spaces.')
    parser.add_argument('--dir', help='Specify the directory to store the downloaded information. (Use with --target or --album)')
    parser.add_argument('--debug', choices=('info','debug'), help='Log extra debug information to pg.log')

    args = parser.parse_args()

    # setup logging
    if args.debug == 'info':
        logging.basicConfig(filename='pg.log',
                            filemode='w',
                            level=logging.INFO)
    elif args.debug == 'debug':
        logging.basicConfig(filename='pg.log',
                            filemode='w',
                            level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    logger = logging.getLogger('photograbber')

    # Login
    if args.token is None:
        browser = raw_input("Open Browser [y/n]: ")
        if browser == 'y':
            facebook.request_token()
            time.sleep(1)
        args.token = raw_input("Enter Token: ")

    graph = facebook.GraphAPI(args.token)
    helper = helpers.Helper(graph)
    #import pdb; pdb.set_trace()

    # --list-targets {'me','friends','pages','following','all'}
    target_list = []
    if args.list_targets == 'me':
        my_info = helper.get_me()
        target_list.append(my_info)
    elif args.list_targets == 'friends':
        target_list.extend(helper.get_friends('me'))
    elif args.list_targets == 'pages':
        target_list.extend(helper.get_pages('me'))
    elif args.list_targets == 'following':
        target_list.extend(helper.get_subscriptions('me'))
    elif args.list_targets == 'all':
        my_info = graph.get_me()
        target_list.append(my_info)
        target_list.extend(helper.get_friends('me'))
        target_list.extend(helper.get_pages('me'))
        target_list.extend(helper.get_subscriptions('me'))

    if args.list_targets is not None:
        for target in target_list:
            print ('%(id)s:"%(name)s"' % target).encode('utf-8')
        return

    # --list_albums <object_id 1> ... <object_id n>
    if args.list_albums is not None:
        for target in args.list_albums:
            album_list = helper.get_album_list(target)
            for album in album_list:
                print ('%(id)s:"%(name)s"' % album).encode('utf-8')
        return

    # TODO: find a directory to store downloads
    if args.dir is None:
        args.dir = raw_input("Download Directory: ")

    # --album <object_id 1> ... <object_id n>
    for album in args.album:
        data = helper.get_album(album)

    # --target <object_id 1> ... <object_id n>
    for target in args.target:
        # if user album
        data = helper.get_albums(target)
        # if tagged
        data = helper.get_tagged(target, full=False)
        # if tagged and full albums
        data = helper.get_tagged(target, full=True)

    # save data to a file
    # download files from each album


    # everything below this can be deleted once album and target are completed
    #
    #
    #
    # Download Potential Targets
    if args.identity is None:
        print "Finding Friends..."
        friends = graph.get_object('me/friends', 5000)

        print "Finding Subscriptions..."
        subscriptions = graph.get_object('me/subscribedto', 5000)

        print "Finding Likes..."
        likes = graph.get_object('me/likes', 5000)

        # Identify which ones id's target
        args.identity = []
        a = True
        while a :
            b = raw_input("target identity: ")
            if (b == ""):
                a = False
            else:
                args.identity.append(b)

    # Get All info
    for id in args.identity:
        data = {}
        try:
            # all tagged photos
            print "Retrieving Tagged Photo Info..."
            unsorted = graph.get_object('%s/photos' % id, 100)
            print "total: %d" % len(unsorted)

            # sort into albums
            # this needs work...
            while len(unsorted) > 0:
                aid = '%s' % find_album(unsorted[0]['id'], graph)
                data[aid] = graph.get_object(aid, 100)
                pids = find_album_photos(aid, graph)

                oids = []
                for pid in pids:
                    oids.append('%s' % pid['object_id'])

                partial_sort = [pic for pic in unsorted if pic['id'] in oids]
                print len(partial_sort)
                data[aid]['photos'] = partial_sort
                unsorted = [pic for pic in unsorted if not pic['id'] in oids]

            # all uploaded albums
            print "Retrieving Album Info..."
            owner_albums = graph.get_object('%s/albums' % id, 100)
            print "total: %d" % len(albums)

            # all photos from an album
            for album in owner_albums:
                print "Album %s" % album['id']
                photos = graph.get_object('%s/photos' % album['id'], 100)
                print "total: %d" % len(data)

            # the actual download
            # the safe the metadata

        except Exception, e:
            raise

if __name__ == "__main__":
    main()
