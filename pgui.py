import wx
from gui.wxFrameLogin import wxFrameLogin
from gui.wxFrameToken import wxFrameToken
from gui.wxFrameChooser import wxFrameChooser
from gui.wxFrameOptions import wxFrameOptions
from gui.wxFrameDownload import wxFrameDownload

import facebook
import helpers
import downloader

import logging
import threading


myEVT_UPDATE_STATUS = wx.NewEventType()
EVT_UPDATE_STATUS = wx.PyEventBinder(myEVT_UPDATE_STATUS, 1)

class UpdateStatusEvent(wx.PyCommandEvent):
    """Event to signal a status update is ready"""
    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value form the event.

        @return: the value of this event
        """
        return self._value

class ProcessThread(threading.Thread):
    def __init__(self, parent, config, helper):
        """
        @param parent: The gui object that should recieve updates
        @param config: dictionary of download config
        @param helper: facebook connnection
        """
        threading.Thread.__init__(self)
        self._parent = parent
        self._config = config
        self._helper = helper

    def run(self):
        """Overrides Thread.run.  Called by Thread.start()."""
        self._helper.process(self._config, self.update)

    def update(self, text):
        evt = UpdateStatusEvent(myEVT_UPDATE_STATUS, -1, text)
        wx.PostEvent(self._parent, evt)

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

        # CODE BELOW BLOCKS, CREATE WORKER THREAD
        my_info = self.helper.get_me()
        if my_info == False:
            self.logger.error('Provided Token Failed: %s' % self.token)
            self.__errorDialog('Invalid Token.  Please re-authenticate with Facebook and try again.')
            return

        self.target_list.append(my_info)
        self.target_list.extend(self.helper.get_friends('me'))
        self.target_list.extend(self.helper.get_pages('me'))
        self.target_list.extend(self.helper.get_subscriptions('me'))
        # CODE ABOVE BLOCKS, CREAT WORKER THREAD

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
        self.current_frame.Begin()

    def beginDownload(self, update):
        # TODO: problem - GUI blocked on this
        # process each target

        config = {}
        config['dir'] = self.directory
        config['targets'] = self.targets
        config['u'] = self.u
        config['t'] = self.t
        config['c'] = self.c
        config['a'] = self.a

        self.Bind(EVT_UPDATE_STATUS, update)

        worker = ProcessThread(self, config, self.helper)
        worker.start()

# end of class PhotoGrabberGUI

def start():
    #PhotoGrabber = PhotoGrabberGUI(redirect=True, filename=None) # replace with 0 to use pdb
    PhotoGrabber = PhotoGrabberGUI(0)
    PhotoGrabber.MainLoop()
