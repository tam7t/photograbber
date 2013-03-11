#!/usr/bin/env python
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

import facebook
import helpers
import downloader

import argparse
import time
import logging
import os

# help strings
helps = {}
helps['u'] = 'Download all albums uploaded by the targets. (Use with --target)'
helps['t'] = 'Download all photos with the target tagged. (Use with --target)'
helps['c'] = 'Download full comment data. (Use with --target)'
helps['a'] = 'Download full album, even if just 1 photo has the tagged target. (Use with --target)'
helps['gui'] =  'Use wx based GUI'
helps['token'] = 'Specify the OAuth token used to authenticate with Facebook.'
helps['list-targets'] ='Display names and object_id\'s of potential targets'
helps['list-albums'] = 'List the albums uploaded by a target.  Separate the object_id\'s of targets with spaces.'
helps['target'] = 'Download targets. Separate the object_id\'s of people or likes with spaces.'
helps['album'] = 'Download full albums.  Separate the object_id\'s of the albums with spaces.'
helps['dir'] = 'Specify the directory to store the downloaded information. (Use with --target or --album)'
helps['debug'] = 'Log extra debug information to pg.log'

def print_func(text):
    print text

def main():
    # parse arguements
    parser = argparse.ArgumentParser(description="Download Facebook photos.")
    parser.add_argument('--gui', action='store_true', help=helps['gui'])
    parser.add_argument('--token', help=helps['token'])
    parser.add_argument('--list-targets', choices=('me','friends','likes','following','all'), help=helps['list-targets'])
    parser.add_argument('--list-albums', nargs='+', help=helps['list-albums'])
    parser.add_argument('--target', nargs='+', help=helps['target'])
    parser.add_argument('-u', action='store_true', help=helps['u'])
    parser.add_argument('-t', action='store_true', help=helps['t'])
    parser.add_argument('-c', action='store_true', help=helps['c'])
    parser.add_argument('-a', action='store_true', help=helps['a'])
    parser.add_argument('--album', nargs='+', help=helps['album'])
    parser.add_argument('--dir', help=helps['dir'])
    parser.add_argument('--debug', choices=('info','debug'), help=helps['debug'])

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

    logger.info('Arguments parsed, logger configured.')

    # GUI
    if args.gui:
        logger.info('Starting GUI.')
        import pgui
        pgui.start()
        logger.info('GUI completed, exiting.')
        exit()

    # Login
    if args.token is None:
        logger.info('No token provided.')
        browser = raw_input("Open Browser [y/n]: ")
        if browser == 'y':
            logger.info('Opening default browser.')
            facebook.request_token()
            time.sleep(1)
        args.token = raw_input("Enter Token: ")

    logger.info('Provided token: %s' % args.token)

    # TODO: check if token works, if not then quit
    graph = facebook.GraphAPI(args.token)
    helper = helpers.Helper(graph)

    # check if token works
    my_info = helper.get_me()
    if not my_info:
        logger.error('Provided Token Failed: %s' % args.token)
        print 'Provided Token Failed: OAuthException'
        exit()

    # --list-targets {'me','friends','likes','following','all'}
    target_list = []
    if args.list_targets == 'me':
        target_list.append(my_info)
    elif args.list_targets == 'friends':
        target_list.extend(helper.get_friends('me'))
    elif args.list_targets == 'likes':
        target_list.extend(helper.get_likes('me'))
    elif args.list_targets == 'following':
        target_list.extend(helper.get_subscriptions('me'))
    elif args.list_targets == 'all':
        target_list.append(my_info)
        target_list.extend(helper.get_friends('me'))
        target_list.extend(helper.get_likes('me'))
        target_list.extend(helper.get_subscriptions('me'))

    if args.list_targets is not None:
        logger.info('Listing available targets.')
        for target in target_list:
            print ('%(id)s:"%(name)s"' % target).encode('utf-8')
        return

    # --list_albums <object_id 1> ... <object_id n>
    if args.list_albums is not None:
        logger.info('Listing available albums.')
        for target in args.list_albums:
            album_list = helper.get_album_list(target)
            for album in album_list:
                print ('%(id)s:"%(name)s"' % album).encode('utf-8')
        return

    # --dir <full path to download location>
    if args.dir is None:
        current_dir = unicode(os.getcwd())
        args.dir = unicode(raw_input("Download Location [%s]: " % current_dir))
        if args.dir == '':
            args.dir = current_dir
    else:
        args.dir = unicode(args.dir)

    logger.info('Download Location: %s' % args.dir)

    # --album <object_id 1> ... <object_id n>
    if args.album is not None:
        logger.info('Downloading albums.')
        for album in args.album:
            # note, doesnt manually ask for caut options for album
            print 'Retrieving album data: %s...' % album
            data = helper.get_album(album, comments=args.c)
            print 'Downloading photos'
            downloader.save_album(data, args.dir)
        return

    # --target <object_id 1> ... <object_id n>
    if args.target is None:
        args.target = []
        args.target.append(raw_input("Target: "))

    # get options
    if not args.c and not args.a:
        if not args.u and not args.t:
            print ''
            print 'Options'
            print '-------'
            print 'u: %s' % helps['u']
            print 't: %s' % helps['t']
            print 'c: %s' % helps['c']
            print 'a: %s' % helps['a']
            opt_str = raw_input("Input Options (e.g. 'cau' or 'caut'):")
            if 'u' in opt_str:
                args.u = True
            if 't' in opt_str:
                args.t = True
            if 'c' in opt_str:
                args.c = True
            if 'a' in opt_str:
                args.a = True

    # TODO: logger print caut options, logger duplicate print info's

    config = {}
    config['dir'] = args.dir
    config['targets'] = args.target
    config['u'] = args.u
    config['t'] = args.t
    config['c'] = args.c
    config['a'] = args.a

    helper.process(config, print_func)

if __name__ == "__main__":
    main()
