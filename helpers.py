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
import threading
import repeater
import requests
import Queue
import os
import time
import re
import shutil
import json  

log = logging.getLogger('pg.%s' % __name__)

class PeopleGrabber(object):
    def __init__(self, graph):
        self.graph = graph

    def get_info(self, id):
        request = {'path':'%s' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        return self.graph.get_data(rid)
    
    def get_friends(self, id):
        request = {'path':'%s/friends' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        a = self.graph.get_data(rid)
        return a

    def get_subscriptions(self, id):
        request = {'path':'%s/subscribedto' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        return self.graph.get_data(rid)
        
    def get_likes(self, id):
        request = {'path':'%s/likes' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        return self.graph.get_data(rid)


class AlbumGrabber(object):
    def __init__(self, graph):
        self.graph = graph

    def get_info(self, id):
        request = {'path':'%s' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        return self.graph.get_data(rid)

    def list_albums(self, id):
        request = {'path':'%s/albums' % id}
        rid = self.graph.make_request(request)
        while self.graph.request_active(rid):
            time.sleep(1)
        return self.graph.get_data(rid)
        
    def _get_node_comments(self, node, comments):
        if not comments:
            # correct tags
            try:
                node['tags'] = node['tags']['data']
            except Exception as e:
                pass
                
            # correct likes
            try:
                node['likes'] = node['likes']['data']
            except Exception as e:
                pass

            # correct comments
            try:
                node['comments'] = node['comments']['data']
            except Exception as e:
                pass
            return
        
        # get node tags
        try:
            url = node['tags']['paging']['next']
            r = {'url':url}
            node['tags_rid'] = self.graph.make_request(r)
        except Exception as e:
            pass
            
        # get node likes
        try:
            url = node['likes']['paging']['next']
            r = {'url':url}
            node['likes_rid'] = self.graph.make_request(r)
        except Exception as e:
            pass

        # get node comments
        try:
            url = node['comments']['paging']['next']
            r = {'url':url}
            node['comments_rid'] = self.graph.make_request(r)
        except Exception as e:
            pass

        # correct tags
        try:
            node['tags'] = node['tags']['data']
        except Exception as e:
            pass
            
        # correct likes
        try:
            node['likes'] = node['likes']['data']
        except Exception as e:
            pass

        # correct comments
        try:
            node['comments'] = node['comments']['data']
        except Exception as e:
            pass
    
    def _fulfill_album_requests(self, album):
        """Does not fulfil 'photos_rid' since that may require additional
        requests."""
        
        wait = 0
        # fulfill all remaining data requests
        if 'likes_rid' in album:
            rid = album['likes_rid']
            if self.graph.request_active(rid):
                wait += 1
            else:
                try:
                    album['likes'].extend(self.graph.get_data(rid))
                except Exception as e:
                    log.exception(e)
                finally:
                    album.pop('likes_rid', None)

        if 'comments_rid' in album:
            rid = album['comments_rid']
            if self.graph.request_active(rid):
                wait += 1
            else:
                try:
                    album['comments'].extend(self.graph.get_data(rid))
                except Exception as e:
                    log.exception(e)
                finally:
                    album.pop('comments_rid', None)

        for photo in album['photos']:
            if 'tags_rid' in photo:
                rid = photo['tags_rid']
                if self.graph.request_active(rid):
                    wait += 1
                else:
                    try:
                        photo['tags'].extend(self.graph.get_data(rid))
                    except Exception as e:
                        log.exception(e)
                    finally:
                        photo.pop('tags_rid', None)
                    
            if 'likes_rid' in photo:
                rid = photo['likes_rid']
                if self.graph.request_active(rid):
                    wait += 1
                else:
                    try:
                        photo['likes'].extend(self.graph.get_data(rid))
                    except Exception as e:
                        log.exception(e)
                    finally:
                        photo.pop('likes_rid', None)

            if 'comments_rid' in photo:
                rid = photo['comments_rid']
                if self.graph.request_active(rid):
                    wait += 1
                else:
                    try:
                        photo['comments'].extend(self.graph.get_data(rid))
                    except Exception as e:
                        log.exception(e)
                    finally:
                        photo.pop('comments_rid', None)

        return wait
    
    def _finish_albums(self, albums, comments, focus=None):
        # append photos to album & request photo info
        oldwait = 0
        while True:
            photos_done = True
            wait = 0
            for album in albums:
                # skip if photos already done
                if 'photos_rid' not in album:
                    continue
                
                # check if request is done
                rid = album['photos_rid']
                if self.graph.request_active(rid):
                    photos_done = False
                    wait += 1
                else:
                    try:
                        album['photos'] = self.graph.get_data(rid)
                    except Exception as e:
                        log.error('Photos request unsuccessful for album: %s' % album['id'])
                        log.exception(e)
                        album['photos'] = []
                    finally:
                        album.pop('photos_rid', None)
                    
                    if focus is not None:
                        # remove photos that we don't care about
                        album['photos'] = [photo for photo in album['photos'] if photo['id'] in focus]

                    for photo in album['photos']:
                        self._get_node_comments(photo, comments)

            if photos_done: break
            if wait != oldwait:
                log.info('Waiting on %d photos requests.' % wait)
            oldwait = wait
            time.sleep(1)
            
        log.info('All photos found.  Waiting on remaining data requests.')

        # fulfill all remaining data requests
        oldwait = 0
        while True:
            wait = 0
            for album in albums:
                wait += self._fulfill_album_requests(album)

            if wait is 0: break
            if wait != oldwait:
                log.info('Waiting on %d requests.' % wait)
            oldwait = wait
            time.sleep(1)

        return albums

    def get_target_albums(self, id, comments=True):
        albums = []
        
        # request list of albums
        request = {'path':'%s/albums' % id}
        rid = self.graph.make_request(request)
        
        # iterate over albums, requesting photos & comments
        while True:
            # request photos from albums
            temp = self.graph.get_data(rid)          # raises exception
            if temp is None:
                temp = []

            for album in temp:
                aid = album['id']
                albums.append(album)
                
                # get album photos
                r = {'path':'%s/photos' % aid}
                album['photos_rid'] = self.graph.make_request(r)
                
                # queue album metadata
                self._get_node_comments(album, comments)
            
            # break loop when no more request data
            active = self.graph.request_active(rid)
            more_data = self.graph.has_data(rid)
            if not active and not more_data: break
            time.sleep(1)
            
        return self._finish_albums(albums, comments)
   
    def get_albums_by_id(self, albums, comments=True, focus=None):
        # albums = [ {'id':<id>, 'photos':[<photo>, <photo>]} , ... ]
        
        # put in a request for each album
        for album in albums:
            request = {'path':'%s' % album['id']}
            rid = self.graph.make_request(request)
            album['album_rid'] = rid
            
            request = {'path':'%s/photos' % album['id']}
            rid = self.graph.make_request(request)
            album['photos_rid'] = rid

        # fulfill album requests
        oldwait = 0
        while True:
            wait = 0
            for album in albums:
                if 'album_rid' in album:
                    rid = album['album_rid']
                    if self.graph.request_active(rid):
                        wait += 1
                    else:
                        try:
                            temp = self.graph.get_data(rid)
                        except Exception as e:
                            log.exception(e)
                            temp = album
                            temp.pop('album_rid', None)

                        try:
                            album.update(temp)
                            album.pop('album_rid', None)
                        except Exception as e:
                            log.exception(e)
                            import pdb; pdb.set_trace()
                        self._get_node_comments(album, comments)

            if wait is 0: break
            if wait != oldwait:
                log.info('Waiting on %d album requests.' % wait)
            oldwait = wait
            time.sleep(1)

        # get node comments on album
        return self._finish_albums(albums, comments, focus)

    def get_tagged(self, id, comments=False, full=True):
        """Get all photos where argument id is tagged.

        id: the object_id of target
        comments: set to True to retrieve all comments
        full: get all photos from all album the user is tagged in
        """

        log.info('get_tagged: %s' % id)
        
        # request list of albums
        request = {'path':'%s/photos' % id}
        rid = self.graph.make_request(request)
        
        while self.graph.request_active(rid):
            time.sleep(1)

        unsorted = self.graph.get_data(rid)     # raises exception

        log.info('tagged in %d photos' % len(unsorted))
        
        unsorted_ids = [x['id'] for x in unsorted]
        album_ids = self.find_album_ids(unsorted_ids)

        data = []

        log.info('%d photos in %d albums' % 
                         (len(unsorted_ids), len(album_ids)))

        for album_id in album_ids:
            album = {}
            album['id'] = album_id
            data.append(album)
        
        if full:
            data = self.get_albums_by_id(data, comments)
        else:
            data = self.get_albums_by_id(data, comments, focus=unsorted_ids)

        # clear out album photos
        for album in data:
            photo_ids = [pic['id'] for pic in album['photos']]
            # remove id's from unsorted that are in the album
            unsorted = [pic for pic in unsorted if pic['id'] not in photo_ids]
        
        # anything not claimed under album_ids will fall into fake album
        if len(unsorted) > 0:
            empty_album = {}
            empty_album['id'] = '0'
            empty_album['name'] = 'Unknown'
            empty_album['photos'] = unsorted

            for photo in empty_album['photos']:
                self._get_node_comments(photo, comments)

            wait = 0
            while True:
                wait = self._fulfill_album_requests(empty_album)
                if wait is 0: break
                time.sleep(1)

            data.append(empty_album)

        return data

    def find_album_ids(self, picture_ids):
        """Find the albums that contains pictures.

        The picture_id arguement must be a list of photo object_id's.

        Returns a list of album object_id's.  If permissions for the album do
        not allow for album information to be retrieved then it is omitted
        from the list.
        """

        q = ''.join(['SELECT object_id, aid FROM album WHERE aid ',
                     'IN (SELECT aid FROM photo WHERE object_id IN (%s))'])

        ids = []
        rids = []
        
        # split query into 25 pictures at a time
        for i in range(len(picture_ids) / 25 + 1):
            pids = ','.join(picture_ids[i * 25:(i+1) * 25])
            request = {'query':q % pids}
            rid = self.graph.make_request(request)
            rids.append(rid)

        while True:
            wait = 0
            for rid in rids:
                if self.graph.request_active(rid):
                    wait += 1
                else:
                    try:
                        new_ids = self.graph.get_data(rid)
                        new_ids = [x['object_id'] for x in new_ids]
                    except Exception as e:
                        bad_query = q % pids
                        log.error('query: %s' % bad_query)
                        log.exception(e)
                        new_ids = []

                    ids = list(set(ids+new_ids))
            if wait is 0: break
            time.sleep(1)

        return ids
        
class DownloaderThread(threading.Thread):
    def __init__(self, q):
        """make many of these threads.
        
        pulls tuples (photo, album_path) from queue to download"""
        
        threading.Thread.__init__(self)
        self.daemon=True
        self.q = q

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
                log.info('downloading:%s' % web_path)
                try:
                    picout.write(self._download(web_path))
                finally:
                    picout.close()

                # correct file time
                created_time = time.strptime(photo['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
                time_int = int(time.mktime(created_time))
                os.utime(save_path, (time_int,) * 2)
            except Exception as e:
                log.exception(e)

            self.q.task_done()

class DownloadPool(object):
    def __init__(self):
        self.q = Queue.Queue()

    def add_thread(self):
        t=DownloaderThread(self.q)
        t.start()
    
    def get_queue(self):
        return self.q

    def save_album(self, album, path):
        # recursively make path
        # http://serverfault.com/questions/242110/which-common-charecters-are-illegal-in-unix-and-windows-filesystems
        #
        # NULL and / are not valid on EXT3
        # < > : " / \ | ? * are not valid Windows
        # prohibited characters in order:
        #   * " : < > ? \ / , NULL
        #
        # '\*|"|:|<|>|\?|\\|/|,|'
        # add . for ... case, windows does not like ellipsis
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
            photo['path'] = '%s' % photo['path'].split('?')[0] # remove any extra arguement nonsense from end of url

            self.q.put( (photo,path) )

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
            log.error(e)

class ProcessThread(threading.Thread):
    def __init__(self, albumgrab, config, pool):
        threading.Thread.__init__(self)
        self.daemon=True

        self.albumgrab = albumgrab
        self.config = config
        self.pool = pool # downloadpool, must have threads already running
        self.msg = "Downloading..."
        self.pics = 0
        self.total = 0

    def run(self):
        """Collect all necessary information and download all files"""

        savedir = self.config['dir']
        targets = self.config['targets']
        u = self.config['u']
        t = self.config['t']
        c = self.config['c']
        a = self.config['a']

        log.info("%s" % self.config)

        for target in targets:
            target_info = self.albumgrab.get_info(target)
            data = []
            u_data = []

            # get user uploaded photos
            if u:
                self.msg = 'Retrieving %s\'s album data...' % target_info['name']
                u_data = self.albumgrab.get_target_albums(target, comments=c)

            t_data = []
            # get tagged
            if t:
                self.msg = 'Retrieving %s\'s tagged photo data...' % target_info['name']
                t_data = self.albumgrab.get_tagged(target, comments=c, full=a)

            if u and t:
                # list of user ids
                u_ids = [album['id'] for album in u_data]
                # remove tagged albums if part of it is a user album
                t_data = [album for album in t_data if album['id'] not in u_ids]

            data.extend(u_data)
            data.extend(t_data)
            
            # find duplicate album names
            for album in data:
                if 'name' not in album or 'from' not in album:
                    log.error('Name not in album: %s' % album)

            # idea, folder name = album (if from target) otherwise
            # also, have 'process data, &args' options for get_target_albums, etc so we can download
            # before waiting on all data

            data = [album for album in data if len(album['photos']) > 0]
            names = [album['name'] for album in data]
            duplicate_names = [name for name, count in collections.Counter(names).items() if count > 1]
            for album in data:
                if album['name'] in duplicate_names:
                    album['folder_name'] = '%s - %s' % (album['name'], album['from']['name'])
                else:
                    album['folder_name'] = album['name']

            self.total = 0
            for album in data:
                self.total = self.total + len(album['photos'])

            self.msg = 'Downloading %d photos...' % self.total

            for album in data:
                path = os.path.join(savedir,unicode(target_info['name']))
                self.pool.save_album(album, path)

            log.info('Waiting for childeren to finish.')
            
            self.pool.get_queue().join()

            log.info('DownloaderThreads completed.')
            log.info('Albums: %s' % len(data))
            log.info('Pics: %s' % self.total)

            self.msg = '%d photos downloaded!' % self.total
    
    def status(self):
        return self.msg
