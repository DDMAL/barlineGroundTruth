# How does the mouse position change when using a scrolled window
# How do canvas drawing functions work, really
import sys
import wx
from gtruth_sorts import *

ID_ZOOM_IN  = wx.ID_HIGHEST + 1
ID_ZOOM_OUT = wx.ID_HIGHEST + 2

class MyPanel(wx.Panel):
    '''
    A simple panel.
    '''
    def __init__(self,parent,pos=(0,0),size=(0,0)):
        wx.Panel.__init__(self,parent,pos=pos,size=size,\
                style=wx.BORDER_SIMPLE)

        # Make click events responded to properly
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnLeftDown(self, evt):
        self.GetParent().ProcessEvent(evt)

class Rect:
    '''
    Represents a rectangle.
    '''
    def __init__(self,posx,posy,szx,szy):
        self.pos = (posx,posy)
        self.size = (szx,szy)

    def GetSize(self):
        return self.size

    def GetPosition(self):
        return self.pos

    def GetArea(self):
        return self.size[0] * self.size[1]

    def SetSize(self,size):
        self.size = size

    def SetPosition(self,pos):
        self.pos = pos

    def GetBox(self):
        '''
        returns tuple as (posx, posy, sizex, sizey)
        '''
        return (self.pos[0], self.pos[1], self.size[0], self.size[1])

class MyScrollingWindow(wx.ScrolledWindow):
    '''
    How does scrolling affect mouse position.
    '''
    def __init__(self, parent, id=-1):
        wx.ScrolledWindow.__init__(self, parent, size=(500,500))
        self.parent = parent

        self.SetScrollRate(20,20)
        # set some size larger than the window to scroll to
        self.SetVirtualSize((1000,1000))

        # bind draw event
        self.Bind(wx.EVT_PAINT,  self.OnPaint)

        # bind mouse events
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnControlClick)

        # Some bogus panels to draw
        self.panels = [Rect(100,200,20,30),
                        Rect(50,300,50,60)]

        # load a default image
        self.bmp = wx.Bitmap("/Users/nickesterer/Documents/"+\
                    "barlineGroundTruth/study/images/Chord_1000_random.tiff",\
                    wx.BITMAP_TYPE_TIF)

        # for zooming, start at original size
        self.userscale = (1.0,1.0)

        # The panel we are currently resizing
        self.curpanel = None

        # Store state of left mouse button
        self.leftdown = False

        # The point at which we first clicked with the left mouse button
        # during a drawing or resizing
        # We store this so we can draw boxes whose sizes are relative to
        # the first position clicked on
        self.leftdownorigx = 0
        self.leftdownorigy = 0

        self.Show(True)
        self.Refresh()

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        dc.SetUserScale(*self.userscale)
        if self.bmp != None:
            dc.DrawBitmap(self.bmp, 0, 0, True)
        for p in self.panels:
            dc.SetBrush(wx.Brush('WHITE',\
                    style=wx.BRUSHSTYLE_TRANSPARENT))
            dc.SetPen(wx.Pen('BLUE',\
                    width=3, style=wx.PENSTYLE_SOLID))
            dc.DrawRectangle(*p.GetBox())

    def OnLeftDown(self, evt):
        '''
        Start drawing a rectangle.
        If shift is down, edit an old panel.
        '''

        if self.leftdown ==  False:

            self.CaptureMouse()

            evtx, evty = evt.GetPosition()

            scrolledevtx, scrolledevty = \
                self.CalcScrolledPosition(evt.GetPosition())

            unscrolledevtx, unscrolledevty = \
                self.CalcUnscrolledPosition(evt.GetPosition())

            sys.stderr.write("Event position: (%d,%d)\n" % (evtx,evty)
                    + "\tScrolled Position(%d,%d)\n" % \
                            (scrolledevtx,scrolledevty)
                    + "\tUnscrolled Position(%d,%d)\n" % \
                            (unscrolledevtx,unscrolledevty))

            vsx, vsy = self.GetViewStart()

            spux, spuy = self.GetScrollPixelsPerUnit()
            sys.stderr.write("View Start: (%d,%d)\n"%\
                    (vsx * spux, vsy * spuy))

            self.leftdown = True 

            if evt.ShiftDown():

                rects = sort_by_area(self.panels)

                self.curpanel = find_smallest_enclosing_rect(rects,\
                        evt.GetPosition())

                if self.curpanel == None:
                    self.leftdown = False
                    self.ReleaseMouse()
                    return

                self.leftdownorigx, self.leftdownorigy =\
                        self.curpanel.GetPosition()

            else:

                self.leftdownorigx, self.leftdownorigy =\
                         (unscrolledevtx/self.userscale[0],\
                            unscrolledevty/self.userscale[1])

                self.panels.append(Rect(self.leftdownorigx,\
                        self.leftdownorigy,0,0))

                self.curpanel = self.panels[-1]

            self.Refresh()
            self.ReleaseMouse()
        
    def OnControlClick(self, evt):
        '''
        Destroy the smallest rectangle beneath the mouse.
        '''

        self.CaptureMouse()

        unscrolledevtx, unscrolledevty = \
            self.CalcUnscrolledPosition(evt.GetPosition())

        x0, y0 = (unscrolledevtx/self.userscale[0],\
                        unscrolledevty/self.userscale[1])

        rects = sort_by_area(self.panels)

        rect = find_smallest_enclosing_rect(rects, (x0,y0))

        if rect == None:
            self.CaptureMouse()
            return

        self.panels.remove(rect)

        del(rect)

        self.Refresh()
        self.ReleaseMouse()

    def OnMouseMove(self, evt):
        '''
        Resize the rectange as we're drawing it, if we're drawing it.
        '''
        if (self.leftdown == True) & (self.curpanel != None):

            self.CaptureMouse()

            unscrolledevtx, unscrolledevty = \
                self.CalcUnscrolledPosition(evt.GetPosition())

            x0, y0 = (unscrolledevtx/self.userscale[0],\
                        unscrolledevty/self.userscale[1])

            # Some logic to handle all start and end drawing motions
            if x0 > self.leftdownorigx:
                if y0 > self.leftdownorigy:
                    pos = (self.leftdownorigx, self.leftdownorigy)
                    size = (x0 - self.leftdownorigx,\
                            y0 - self.leftdownorigy)
                else:
                    pos = (self.leftdownorigx, y0)
                    size = (x0 - self.leftdownorigx,
                            self.leftdownorigy - y0)
            else:
                if y0 > self.leftdownorigy:
                    pos = (x0,self.leftdownorigy)
                    size = (self.leftdownorigx - x0,\
                            y0 - self.leftdownorigy)
                else:
                    pos = (x0, y0)
                    size = (self.leftdownorigx - x0,\
                            self.leftdownorigy - y0)

            self.curpanel.SetSize(size)
            self.curpanel.SetPosition(pos)

            self.Refresh()
            self.ReleaseMouse()
    
    def OnLeftUp(self, evt):
        '''
        When left mouse button released, you have a box.
        '''
        if (self.leftdown == True) & (self.curpanel != None):

            self.CaptureMouse()

            unscrolledevtx, unscrolledevty = \
                self.CalcUnscrolledPosition(evt.GetPosition())

            x0, y0 = (unscrolledevtx/self.userscale[0],\
                        unscrolledevty/self.userscale[1])

            curx, cury = self.curpanel.GetPosition()

            # Some logic to handle all start and end drawing motions
            if x0 > self.leftdownorigx:
                if y0 > self.leftdownorigy:
                    pos = (self.leftdownorigx, self.leftdownorigy)
                    size = (x0 - self.leftdownorigx,\
                            y0 - self.leftdownorigy)
                else:
                    pos = (self.leftdownorigx, y0)
                    size = (x0 - self.leftdownorigx,
                            self.leftdownorigy - y0)
            else:
                if y0 > self.leftdownorigy:
                    pos = (x0,self.leftdownorigy)
                    size = (self.leftdownorigx - x0,\
                            y0 - self.leftdownorigy)
                else:
                    pos = (x0, y0)
                    size = (self.leftdownorigx - x0,\
                            self.leftdownorigy - y0)

            self.leftdown = False
            self.curpanel.SetSize(size)
            self.curpanel.SetPosition(pos)
            self.curpanel = None
            self.Refresh()
            self.ReleaseMouse()

class MyFrame(wx.Frame):
    '''
    A base frame for the application.
    '''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)

        # instance of my scrolling window
        self.scrolledwin = MyScrollingWindow(self)

        # create a file menu
        filemenu = wx.Menu()

        # Entry to exit program
        filemenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit the example")

        # entries for zooming in and out
        filemenu.Append(ID_ZOOM_IN, "Zoom In\tAlt-+",\
                "Zoom in the window")
        filemenu.Append(ID_ZOOM_OUT, "Zoom Out\tAlt--",\
                "Zoom out the window")

        # bind zoom in and zoom out methods
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=ID_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=ID_ZOOM_OUT)
        # bind exit command
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)

        # Add menus to menu bar
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        self.SetMenuBar(menubar)

    def OnExit(self, evt):
        self.Close()

    def OnZoomIn(self, evt):
        usx, usy = self.scrolledwin.userscale
        self.scrolledwin.userscale = (usx * 1.1, usy * 1.1)
        self.scrolledwin.Refresh()

    def OnZoomOut(self, evt):
        usx, usy = self.scrolledwin.userscale
        self.scrolledwin.userscale = (usx * 0.9, usy * 0.9)
        self.scrolledwin.Refresh()


class MyApp(wx.App):
    '''
    The app...
    '''
    def OnInit(self):
        self.frame = MyFrame(None,"Scrolling Test")
        self.frame.Show(True)
        return True

app = MyApp()
app.MainLoop()
