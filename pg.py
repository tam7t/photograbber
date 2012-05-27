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
import downloader

import argparse
import time
import logging
import os
import multiprocessing

def main():
    # help strings
    u_help = 'Download all albums uploaded by the targets. (Use with --target)'
    t_help = 'Download all photos with the target tagged. (Use with --target)'
    c_help = 'Download full comment data. (Use with --target)'
    a_help = 'Download full album, even if just 1 photo has the tagged target. (Use with --target)'

    # parse arguements
    parser = argparse.ArgumentParser(description="Download Facebook photos.")
    parser.add_argument('--token', help='Specify the OAuth token used to authenticate with Facebook.')
    parser.add_argument('--list-targets', choices=('me','friends','pages','following','all'), help='Display names and object_id\'s of potential targets')
    parser.add_argument('--list-albums', nargs='+', help='List the albums uploaded by a target.  Separate the object_id\'s of targets with spaces.')
    parser.add_argument('--target', nargs='+', help='Download targets. Separate the object_id\'s of people or pages with spaces.')
    parser.add_argument('-u', action='store_true', help=u_help)
    parser.add_argument('-t', action='store_true', help=t_help)
    parser.add_argument('-c', action='store_true', help=c_help)
    parser.add_argument('-a', action='store_true', help=a_help)
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
        logging.basicConfig(filename='pg.log',
                            filemode='w',
                            level=logging.ERROR)

    logger = logging.getLogger('photograbber')

    # Login
    if args.token is None:
        browser = raw_input("Open Browser [y/n]: ")
        if browser == 'y':
            facebook.request_token()
            time.sleep(1)
        args.token = raw_input("Enter Token: ")

    # TODO: check if token works, if not then quit
    graph = facebook.GraphAPI(args.token)
    helper = helpers.Helper(graph)

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

    # --dir
    if args.dir is None:
        current_dir = unicode(os.getcwd())
        args.dir = unicode(raw_input("Download Location [%s]: " % current_dir))
        if args.dir == '':
            args.dir = current_dir
    else:
        args.dir = unicode(args.dir)

    # --album <object_id 1> ... <object_id n>
    if args.album is not None:
        for album in args.album:
            # note, doesnt manually ask for caut options for album
            data = helper.get_album(album, comments=args.c)
        # download data
        #
        # TODO: call function to download the album
        return

    # --target <object_id 1> ... <object_id n>
    if args.target is None:
        args.target = []
        args.target.append(raw_input("Target: "))

    # get options
    if args.c is False and args.a is False:
        if args.u is False and args.t is False:
            print ''
            print 'Options'
            print '-------'
            print 'u: %s' % u_help
            print 't: %s' % t_help
            print 'c: %s' % c_help
            print 'a: %s' % a_help
            opt_str = raw_input("Input Options (e.g. 'cau' or 'caut'):")
            if 'u' in opt_str:
                args.u = True
            if 't' in opt_str:
                args.t = True
            if 'c' in opt_str:
                args.c = True
            if 'a' in opt_str:
                args.a = True

    # process each target
    for target in args.target:

        target_info = helper.get_info(target)

        data = []

        u_data = []
        # get user uploaded photos
        if args.u:
            print 'Retrieving %s\'s album data...' % target
            u_data = helper.get_albums(target, comments=args.c)

        t_data = []
        # get tagged
        if args.t:
            print 'Retrieving %s\'s tagged photo data...' % target
            t_data = helper.get_tagged(target, comments=args.c, full=args.a)

        for user_album in u_data:
            added = False
            # will the album be added from t_data?
            for tagged_album in t_data:
                if tagged_album['id'] == user_album['id']:
                    added = True
            if not added:
                data.append(user_album)
        data.extend(t_data)

        # download data
        pool = multiprocessing.Pool(processes=5)

        print 'Downloading photos'

        for album in data:
            # TODO: Error where 2 albums with same name exist
            path = os.path.join(args.dir,unicode(target_info['name']))
            pool.apply_async(downloader.save_album,
                            (album,path)
                            ) #callback=
        pool.close()

        logger.info('Waiting for childeren to finish')

        while multiprocessing.active_children():
            time.sleep(1)
        pool.join()

        logger.info('Child processes completed')

        pics = 0
        for album in data:
            pics = pics + len(album['photos'])
        logger.info('albums: %s' % len(data))
        logger.info('pics: %s' % pics)
        logger.info('rtt: %d' % graph.get_stats())

        print 'Complete!'

if __name__ == "__main__":
    main()
