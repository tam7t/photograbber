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

import argparse
import time
import logging
import os

import res

# error when packaging
# https://github.com/kennethreitz/requests/issues/557
os.environ['REQUESTS_CA_BUNDLE'] = res.getpath('requests/cacert.pem')

# help strings
helps = {}
helps['u'] = 'Download all albums uploaded by the target. (Use with --target)'
helps['t'] = 'Download all photos where the target is tagged. (Use with --target)'
helps['c'] = 'Download full comment data. (Use with --target)'
helps['a'] = 'Download the full album, even if tagged in a single photo. (Use with --target and -t)'
helps['cmd'] =  'Use command line instead of Qt GUI'
helps['token'] = 'Specify the OAuth token used to authenticate with Facebook.'
helps['list-targets'] ='Display names and object_id\'s of potential targets'
helps['list-albums'] = 'List the albums uploaded by a target.  Separate the object_id\'s of targets with spaces.'
helps['target'] = 'Download targets. Separate the object_id\'s of people or likes with spaces.'
helps['album'] = 'Download full albums.  Separate the object_id\'s of the albums with spaces.'
helps['dir'] = 'Specify the directory to store the downloaded information. (Use with --target or --album)'
helps['debug'] = 'Log extra debug information to pg.log'

log = logging.getLogger('pg')

def print_func(text):
    if text: print text

def main():
    # parse arguments
    parser = argparse.ArgumentParser(description="Download photos from Facebook.")
    parser.add_argument('--cmd', action='store_true', help=helps['cmd'])
    parser.add_argument('--token', help=helps['token'])
    parser.add_argument('--list-targets', choices=('me','friends','likes','all'), help=helps['list-targets'])
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
    format = "%(asctime)s:%(levelname)s:%(name)s:%(lineno)d:%(message)s"

    logging.basicConfig(filename='pg.log',
                        filemode='w',
                        format=format,
                        level=logging.ERROR)

    if args.debug == 'info':
        logging.getLogger("pg").setLevel(logging.INFO)
    elif args.debug == 'debug':
        logging.getLogger("pg").setLevel(logging.DEBUG)

    log.info('Arguments parsed, log configured.')
    
    log.error('basedir: %s' % res.getpath() )
    
    # GUI
    if not args.cmd:
        log.info('Starting GUI.')
        import pgui
        pgui.start()
        log.info('GUI completed, exiting.')
        exit()

    # Login
    if args.token is None:
        log.info('No token provided.')
        browser = raw_input("Open Browser [y/n]: ")
        if not browser.isalnum(): raise ValueError('Input must be alphanumeric.')
        if browser == 'y':
            log.info('Opening default browser.')
            facebook.request_token()
            time.sleep(1)
        args.token = raw_input("Enter Token: ")
    if not args.token.isalnum(): raise ValueError('Input must be alphanumeric.')

    # setup facebook API objects
    graph = facebook.GraphAPI(args.token)
    graph.start()
    peoplegrab = helpers.PeopleGrabber(graph)
    albumgrab = helpers.AlbumGrabber(graph)
    
    # ensure token is removed from logs...
    log.info('Provided token: %s' % args.token)

    # check if token works
    my_info = peoplegrab.get_info('me')
    if not my_info:
        log.error('Provided Token Failed: %s' % args.token)
        print 'Provided Token Failed: OAuthException'
        exit()

    # --list-targets {'me','friends','likes','all'}
    target_list = []
    if args.list_targets == 'me':
        target_list.append(my_info)
    elif args.list_targets == 'friends':
        target_list.extend(peoplegrab.get_friends('me'))
    elif args.list_targets == 'likes':
        target_list.extend(peoplegrab.get_likes('me'))
    elif args.list_targets == 'all':
        target_list.append(my_info)
        target_list.extend(peoplegrab.get_friends('me'))
        target_list.extend(peoplegrab.get_likes('me'))

    if args.list_targets is not None:
        log.info('Listing available targets.')
        for target in target_list:
            print ('%(id)s:"%(name)s"' % target).encode('utf-8')
        return

    # --list_albums <object_id 1> ... <object_id n>
    if args.list_albums is not None:
        log.info('Listing available albums.')
        for target in args.list_albums:
            album_list = albumgrab.list_albums(target)
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
    if not os.path.exists(args.dir): raise ValueError('Download Location must exist.')

    log.info('Download Location: %s' % args.dir)

    # --album <object_id 1> ... <object_id n>
    if args.album is not None:
        log.info('Downloading albums.')
        albums = []
        for album in args.album:
            # note, doesnt manually ask for caut options for album
            if not album.isdigit(): raise ValueError('Input must be numeric.')
            print 'Retrieving album data: %s...' % album
            albums.append({'id':album})

        data = albumgrab.get_albums_by_id(albums, comments=args.c)
        
        # todo: filter photos_ids from albums before downloading...
        
        print 'Downloading photos'
        pool = helpers.DownloadPool()
        for a in range(5): pool.add_thread()
        
        # set path to include the name of who uploaded the album
        data = [album for album in data if len(album['photos']) > 0]
        for album in data:
            album['folder_name'] = album['name']
            path = os.path.join(args.dir, unicode(album['from']['name']))
            pool.save_album(album, path)

        pool.get_queue().join()
        return

    # --target <object_id 1> ... <object_id n>
    if args.target is None:
        args.target = []
        args.target.append(raw_input("Target: "))
    
    for target in args.target:
        if not target.isalnum(): raise ValueError('Input must be alphanumeric')

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
            if not opt_str.isalnum(): raise ValueError('Input must be alphanumeric')
            if 'u' in opt_str:
                args.u = True
            if 't' in opt_str:
                args.t = True
            if 'c' in opt_str:
                args.c = True
            if 'a' in opt_str:
                args.a = True

    config = {}
    config['dir'] = args.dir
    config['targets'] = args.target
    config['u'] = args.u
    config['t'] = args.t
    config['c'] = args.c
    config['a'] = args.a

    # download pool
    pool = helpers.DownloadPool()
    for a in range(5): pool.add_thread()

    # process thread
    thread = helpers.ProcessThread(albumgrab, config, pool)
    thread.start()
    
    print 'Please wait while I download your photos...'

    thread.join()

if __name__ == "__main__":
    main()
