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

    def __init__(self, originalWidth, originalHeight, originalPosition=(0,0)):
        self.originalWidth = originalWidth
        self.originalHeight = originalHeight
        self.originalPosition = originalPosition

    def Zoom(self, factor=1.0):
        '''
        Zoom by some factor.
        Values greater than 1 zoom in, values less than 1 zoom out.
        For example 1.1 will make the image 1.1 times bigger than its original
        size, 0.8 will make it 0.8 times bigger (or 1.25 times smaller) than
        its original size.
        It will also move the origin position according to the factor, so if the
        original position was (100,80) and you change the zoom by a factor of
        0.75 (by calling Zoom(0.75)) then the new positon will be set to
        (75,60).
        '''
        if factor < 0:
            raise ValueError('Factor %f less than 0' % (factor))
        self.SetWidth(float(self.originalWidth) * factor)
        self.SetHeight(float(self.originalHeight) * factor)
        newposx, newposy = self.originalPosition
        try:
            self.SetPosition((newposx * factor, newposy * factor))
        except NotImplementedError: 
            pass # if no set position function, just don't set it

class MyBitmap(wx.Bitmap, Zoomer):
    '''
    Subclass of wx.Bitmap that can be "zoomed".
    '''
    def __init__(self, name, type):
        wx.Bitmap.__init__(self, name, type)
        # store original width and height so that we can resize acccordingly
        Zoomer.__init__(self, self.GetWidth(), self.GetHeight())

    def SetPosition(self, *args, **kwargs):
        raise NotImplementedError('The position of MyBitmap cannot be set')

class MyPanel(wx.Panel, Zoomer):
    '''
    Displays a box that can be "zoomed"
    '''
    def __init__(self, parent, pos, size=(0,0), bordercolour='RED'):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos=pos, size=size,\
                style=wx.BORDER_NONE)

        # store parent
        self.parent = parent

        # store original width, height and position so that we can resize acccordingly
        Zoomer.__init__(self, self.GetWidth(), self.GetHeight(),\
            self.GetPosition())
        
        # store border color
        self.bordercolour = bordercolour

        # bind paint function to native callback
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.Enable(True)

        self.Show(True)

        self.Refresh()

    def OnPaint(self, evt):
        '''
        Called by the OS to refresh drawing. Draws the coloured border.
        '''
        dc = wx.PaintDC(self)
        posx, posy = self.GetPosition()
        sizex, sizey = self.GetSize()
        dc.SetBrush(wx.Brush('WHITE',style=wx.BRUSHSTYLE_TRANSPARENT))
        dc.SetPen(wx.Pen(self.bordercolour, width=3, style=wx.PENSTYLE_SOLID))
        dc.DrawRectangle(0, 0, sizex, sizey)

    def SetHeight(self, height):
        # Doesn't include this method so it must be added for zooming to work
        size = self.GetSize()
        self.SetSize((size[0], height))

    def SetWidth(self, width):
        # Doesn't include this method so it must be added for zooming to work
        size = self.GetSize()
        self.SetSize((width, size[1]))

    def GetHeight(self):
        # Doesn't include this method so it must be added for zooming to work
        return self.GetSize()[0]

    def GetWidth(self):
        # Doesn't include this method so it must be added for zooming to work
        return self.GetSize()[1]

    def GetPosition(self):
        # Assumes the parent has the method CalcUnscrolledPosition
        return self.parent.CalcScrolledPosition(wx.Panel.GetPosition(self))

    def SetPosition(self, position):
        # Assumes the parent has the method CalcUnscrolledPosition
        wx.Panel.SetPosition(self, self.parent.CalcScrolledPosition(position))


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

        self.SetScrollRate(20,20)

        # load a default image
        self.bmp = MyBitmap("/Users/nickesterer/Documents/"+\
                    "barlineGroundTruth/study/images/Chord_1000_random.tiff",\
                    wx.BITMAP_TYPE_TIF)

        # Bind paint event so the canvas will be redrawn
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # some test panels
        self.panels = [MyPanel(self, (10,10), (100,100)), MyPanel(self,\
            (20,30),(40,50))]

        self.Show(True)
        self.Refresh()

    def UpdateSizeFromBmp(self):
        self.maxWidth = self.bmp.GetWidth()
        self.maxHeight= self.bmp.GetHeight()
        self.SetVirtualSize((self.maxWidth, self.maxHeight))

    def OnPaint(self, evt):
        '''
        Called by the OS to refresh drawing.
        '''
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        if self.bmp != None:
            dc.DrawBitmap(self.bmp, 0, 0, True)

    def Zoom(self, factor):
        self.bmp.Zoom(factor)
        for p in self.panels:
            p.Zoom(factor)
        self.UpdateSizeFromBmp()
        self.Refresh()

class MyFrame(wx.Frame):
    '''
    Some dumb base of our application.
    '''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)

        # create a file menu
        filemenu = wx.Menu()
        # Entry to exit program
        filemenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit the example")
        # entries for zooming in and out
        filemenu.Append(ID_ZOOM_IN, "Zoom In\tAlt-+",\
                "Zoom in the window")
        filemenu.Append(ID_ZOOM_OUT, "Zoom Out\tAlt--",\
                "Zoom out the window")

        # child window is the window that can zoom
        self.zoomedwin = ZoomingWindow(self)

        # bind zoom in and zoom out methods
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=ID_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=ID_ZOOM_OUT)
        # bind exit command
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)

        # Add menus to menu bar
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        self.SetMenuBar(menubar)

        # how zoomed in are we
        self.zoomfactor = 1.0

    def Zoom(self, factor):
        try:
            self.zoomedwin.Zoom(factor)
        except ValueError:
            print 'Cannot zoom beyond limit.'

    def OnZoomIn(self, evt):
        self.zoomfactor = self.zoomfactor * 1.1
        self.Zoom(self.zoomfactor)

    def OnZoomOut(self, evt):
        self.zoomfactor = self.zoomfactor * 0.9
        self.Zoom(self.zoomfactor)

    def OnExit(self, evt):
        self.Close()

app = MyApp()
app.MainLoop()
