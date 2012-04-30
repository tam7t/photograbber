#!/usr/bin/python

import facebook
import argparse
import time

def query(query_string, graph):
    max_retries = 10
    retries = 0
    while True:
        try:
            return graph.fql(query_string)
        except Exception, e:
            raise
            if retries < max_retries:
                retries += 1
                time.sleep(retries * 2)
            else:
                raise

def find_album(id, graph):
    q = ''.join(['SELECT object_id, aid FROM album WHERE aid ',
                 'IN (SELECT aid FROM photo WHERE object_id=%s)']) % id
    return query(q, graph)[0]['object_id']

def find_album_photos(id, graph):
    q = ''.join(['SELECT object_id, pid FROM photo WHERE aid ',
                 'IN (SELECT aid FROM album WHERE object_id=%s)']) % id
    return query(q, graph)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token')
    parser.add_argument('-i', '--identity', nargs="+")
    args = parser.parse_args()

    # Login
    if args.token is None:
        browser = raw_input("Open Browser [y/n]: ")
        if browser == 'y':
            facebook.request_token()
            time.sleep(1)
        args.token = raw_input("Enter Token: ")

    graph = facebook.GraphAPI(args.token)

    # Download Potential Targets
    if args.identity is None:
        print "Finding Friends..."
        #friends = graph.get_object('me/friends', 5000)

        print "Finding Subscriptions..."
        #subscriptions = graph.get_object('me/subscribedto', 5000)

        print "Finding Likes..."
        #likes = graph.get_object('me/likes', 5000)

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
