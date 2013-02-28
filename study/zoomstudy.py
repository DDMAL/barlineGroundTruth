'''
How do u zoom using wx widgets?
'''

import wx
import abc

ID_ZOOM_IN  = wx.ID_HIGHEST + 1
ID_ZOOM_OUT = wx.ID_HIGHEST + 2

class Zoomer:
    '''
    A class that supports zooming, granted the object that subclasses it has the
    methods:
    self.SetWidth()
    self.SetHeight()
    self.SetPosition()
    Sublassing this will allow you to zoom instances of the class
    '''
    __metaclass__ = abc.ABCMeta

    # We want to guarantee subclasses have these methods
    @abc.abstractmethod
    def SetWidth(self, *args, **kwargs):
        pass
    @abc.abstractmethod
    def SetHeight(self, *args, **kwargs):
        pass
    @abc.abstractmethod
    def SetPosition(self, *args, **kwargs):
        pass

    def __init__(self, originalWidth, originalHeight):
        self.originalWidth = originalWidth
        self.originalHeight = originalHeight

    def Zoom(self, factor=1.0):
        '''
        Zoom by some factor.
        Values greater than 1 zoom in, values less than 1 zoom out.
        For example 1.1 will make the image 1.1 times bigger than its original
        size, 0.8 will make it 0.8 times bigger (or 1/0.8 times smaller) than
        its original size.
        '''
        if factor < 0:
            raise ValueError('Factor %f less than 0' % (factor))
        self.SetWidth(float(self.originalWidth) * factor)
        self.SetHeight(float(self.originalHeight) * factor)

class MyBitmap(wx.Bitmap, Zoomer):
    '''
    Subclass of wx.Bitmap that can be "zoomed".
    '''
    def __init__(self, name, type):
        wx.Bitmap.__init__(self, name, type)
        # store original width and height so that we can resize acccordingly
        Zoomer.__init__(self, self.GetWidth(), self.GetHeight())

    def SetPosition(self, *args, **kwargs):
        pass # you cannot set the posiiton of a bitmap, nor will you need to

class MyApp(wx.App):
    '''
    The main app that contains all the windows
    '''
    def OnInit(self):
        self.frame = MyFrame(None,"Zoom Test")
        self.frame.Show(True)
        return True

class ZoomingWindow(wx.ScrolledWindow):
    '''
    A window that supports zooming.
    '''
    def __init__(self, parent, id=-1):
        wx.ScrolledWindow.__init__(self, parent, size=(500,500))
        self.parent = parent

        # I don't know if this is necessary
        parent.SetBackgroundColour('WHITE')
        self.SetScrollRate(20,20)

        # load a default image
        self.bmp = MyBitmap("/Users/nickesterer/Documents/"+\
                    "barlineGroundTruth/study/images/Chord_1000_random.tiff",\
                    wx.BITMAP_TYPE_TIF)
        self.maxWidth = self.bmp.GetWidth()
        self.maxHeight= self.bmp.GetHeight()
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.bmp.Zoom(0.5)

        # Bind paint event so the canvas will be redrawn
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.Show(True)
        self.Refresh()

    def OnPaint(self, evt):
        '''
        Called by the OS to refresh drawing.
        '''
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        if self.bmp != None:
            dc.DrawBitmap(self.bmp, 0, 0, True)

class MyFrame(wx.Frame):
    '''
    Some dumb base of our application.
    '''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)

        # create a file menu
        filemenu = wx.Menu()
        # entries for zooming in and out
        filemenu.Append(ID_ZOOM_IN, "Zoom In\tShift-Alt-=",\
                "Zoom in the window")
        filemenu.Append(ID_ZOOM_OUT, "Zoom Out\tAlt--",\
                "Zoom out the window")

        # child window is the window that can zoom
        self.zoomedwin = ZoomingWindow(self)

        # bind zoom in and zoom out methods
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=ID_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=ID_ZOOM_OUT)

    def OnZoomIn(self, evt):
        pass

    def OnZoomOut(self, evt):
        pass

app = MyApp()
app.MainLoop()
