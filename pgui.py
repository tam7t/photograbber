import wx
from gui.wxFrameLogin import wxFrameLogin
from gui.wxFrameToken import wxFrameToken
from gui.wxFrameChooser import wxFrameChooser
from gui.wxFrameOptions import wxFrameOptions
from gui.wxFrameDownload import wxFrameDownload

import facebook
import helpers
import downloader

import time
import logging
import os
import multiprocessing

class PhotoGrabberGUI(wx.App):
    """Control and Data Structure for GUI.

    helper - Instance of the facebook object.  Performs Graph API queries.

    target_list - People/pages to download.

    directory - Location to save files.

    current_frame - Current GUI frame (wxFrame).  The PhotoGrabberGUI object is
                    passed to the frame to pass data and issue control follow
                    events.

                    Each frame must implement a Setup() function and call the
                    appropriate PhotoGrabberGui.to* function to advance to next
                    frame.
    """

    logger = logging.getLogger('PhotoGrabberGUI')
    helper = None
    current_frame = None
    target_list = [] # read by GUI to display usernames

    # TODO: document and make more descriptive
    token = None # authentication token to use
    targets = [] # what to actually download
    u = False
    t = False
    c = False
    a = False
    directory = None # directory to store downloads

    def OnInit(self):
        wx.InitAllImageHandlers()
        self.current_frame = wxFrameLogin(None, -1, "")
        self.current_frame.Setup(self)
        self.SetTopWindow(self.current_frame)
        self.current_frame.Show()
        print 'hi'
        return 1

    def __nextFrame(self, frame):
        """Destroy current frame then create and setup the next frame."""
        self.current_frame.Destroy()
        self.current_frame = frame
        self.current_frame.Setup(self)
        self.SetTopWindow(self.current_frame)
        self.current_frame.Show()

    def __errorDialog(self, message):
        msg_dialog = wx.MessageDialog(parent=self.current_frame,
                                      message=message,
                                      caption='Error',
                                      style=wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
                                      )
        msg_dialog.ShowModal()
        msg_dialog.Destroy()


    # workflow functions (called by frames)
    #   login window
    #   token window
    #   chooser window
    #   options window
    #   folder dialog
    #   download status

    def toToken(self):
        facebook.request_token()
        self.__nextFrame(wxFrameToken(None, -1, ""))

    def toChooser(self):
        self.helper = helpers.Helper(facebook.GraphAPI(self.token))

        my_info = self.helper.get_me()
        if my_info == False:
            self.logger.error('Provided Token Failed: %s' % self.token)
            self.__errorDialog('Invalid Token.  Please re-authenticate with Facebook and try again.')
            return

        self.target_list.append(my_info)
        self.target_list.extend(self.helper.get_friends('me'))
        self.target_list.extend(self.helper.get_pages('me'))
        self.target_list.extend(self.helper.get_subscriptions('me'))

        # it is possible that there could be multiple 'Tommy Murphy'
        # make sure to download all different versions that get selected

        self.__nextFrame(wxFrameChooser(None, -1, ""))

    def toOptions(self):
        self.__nextFrame(wxFrameOptions(None, -1, ""))

    def toFolder(self):
        dir_dialog = wx.DirDialog(parent=self.current_frame,
                                  message="Choose a directory:",
                                  style=wx.DD_DEFAULT_STYLE
                                  )

        if dir_dialog.ShowModal() == wx.ID_OK:
            self.directory = dir_dialog.GetPath()
            self.logger.info("Download Directory: %s" % self.directory)
            dir_dialog.Destroy()
            self.toDownload()
        else:
            self.logger.error("Download Directory: None")
            dir_dialog.Destroy()
            # let user know they have to select a directory
            self.__errorDialog('You must choose a directory.')

    def toDownload(self):
        self.__nextFrame(wxFrameDownload(None, -1, ""))

    def beginDownload(self, update):
        # TODO: problem - GUI blocked on this
        # process each target
        for target in self.targets:
            target_info = self.helper.get_info(target)
            data = []
            u_data = []

            # get user uploaded photos
            if self.u:
                update('Retrieving %s\'s album data...' % target)
                u_data = self.helper.get_albums(target, comments=self.c)

            t_data = []
            # get tagged
            if self.t:
                update('Retrieving %s\'s tagged photo data...' % target)
                t_data = self.helper.get_tagged(target, comments=self.c, full=self.a)

            if self.u and self.t:
                # list of user ids
                u_ids = [album['id'] for album in u_data]
                # remove tagged albums if part of it is a user album
                t_data = [album for album in t_data if album['id'] not in u_ids]

            data.extend(u_data)
            data.extend(t_data)

            # download data
            pool = multiprocessing.Pool(processes=5)

            update('Downloading photos')

            for album in data:
                # TODO: Error where 2 albums with same name exist
                path = os.path.join(self.directory,unicode(target_info['name']))
                pool.apply_async(downloader.save_album,
                                (album,path)
                                ) #callback=
            pool.close()

            self.logger.info('Waiting for childeren to finish')

            while multiprocessing.active_children():
                time.sleep(1)
            pool.join()

            self.logger.info('Child processes completed')

            pics = 0
            for album in data:
                pics = pics + len(album['photos'])
            self.logger.info('albums: %s' % len(data))
            self.logger.info('pics: %s' % pics)
            # self.logger.info('rtt: %d' % graph.get_stats())

            update('Complete!')

# end of class PhotoGrabberGUI

def start():
    #PhotoGrabber = PhotoGrabberGUI(redirect=True, filename=None) # replace with 0 to use pdb
    PhotoGrabber = PhotoGrabberGUI(0)
    PhotoGrabber.MainLoop()
