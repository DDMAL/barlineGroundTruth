# How does the mouse position change when using a scrolled window
import sys
import wx

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

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

        # Some bogus panels to get information about
        self.panels = [MyPanel(self,(100,200),(20,30)),
                        MyPanel(self,(50,300),(50,60))]

        for p in self.panels:
            p.Show(True)
            p.Enable(True)
            p.Refresh(True)

        self.Show(True)
        self.Refresh()

    def OnLeftDown(self, evt):
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
        for p in self.panels:
            evtx, evty = p.GetPosition()
            scrolledevtx, scrolledevty = \
            self.CalcScrolledPosition(p.GetPosition())
            unscrolledevtx, unscrolledevty = \
            self.CalcUnscrolledPosition(p.GetPosition())
            sys.stderr.write(\
                    "Rectangle position: (%d,%d)\n" % \
                            (evtx,evty)
                    + "\tScrolled Position(%d,%d)\n" % \
                            (scrolledevtx,scrolledevty)
                    + "\tUnscrolled Position(%d,%d)\n" % \
                            (unscrolledevtx,unscrolledevty))

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
        vsizex, vsizey = self.scrolledwin.GetVirtualSize()
        self.scrolledwin.SetVirtualSize((vsizex+100,vsizey+100))

    def OnZoomOut(self, evt):
        vsizex, vsizey = self.scrolledwin.GetVirtualSize()
        self.scrolledwin.SetVirtualSize((vsizex-100,vsizey-100))


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
