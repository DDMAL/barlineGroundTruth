#!/usr/bin/env python

import wx
import sys
import gtruth_meicreate
from   gtruth_zoom import ZoomerMover
from gtruth_sorts import *
import gamera.core

''' Save to mei file instead of text file. Must append path to meicreate.py to
PYTHONPATH environment variable unless this is run in the same directory as it. '''

helpmess = \
'''\
To open a picture to draw boxes upon, go to
File->Open
and select the image from the file dialog.

To save the boxes that you have drawn onto the picture go to 
File->Save
and then choose a file path and a filename in the file \
dialog (a filename will be suggested to you).

To draw a box onto the picture, click and hold the left mouse \
button. Release the button when you have drawn a box of the size of \
your liking.

To delete a box already drawn, hold down control and click on the \
box you would like to delete. If multiple boxes are beneath the \
cursor, the smallest will be deleted.

To resize a box that has already been drawn, hold down shift and \
click and hold the left mouse button.  Release the button once you \
have resized the box to your liking. Note that you may only change \
the position of the bottom right hand corner, to change any other \
corners, the box must be deleted and redrawn.

There are two kinds of boxes that can be drawn: there are boxes \
that bound the bars and boxes that bound the staves. The former \
are in ren and the latter in green. To toggle between the two \
types, go to
File->(Bar mode | Staff mode)
depending on what mode you are in currently. Note that when \
deleting boxes you will only delete the type of boxes whose mode \
you are in currently. This is also true for the Clear method.

WARNING: If you scroll while drawing a box it will mess up the top \
corner coordinates. If you would like to draw a box larger than the \
screen, simply draw the box as large as you can, let go of the \
mouse button, scroll the window and then shift-click on the box to \
resize it.
'''

# for debugging
__GTRUTH_DEBUG__ = True

# custom event ids
ID_LOAD_BOXES       = wx.ID_HIGHEST + 1
ID_HELP_DLG         = wx.ID_HIGHEST + 2
ID_TOGGLE_RECT_MODE = wx.ID_HIGHEST + 3
ID_ZOOM_IN          = wx.ID_HIGHEST + 4
ID_ZOOM_OUT         = wx.ID_HIGHEST + 5

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

class MyApp(wx.App):
    '''
    The main app that contains all of the child windows.
    '''
    def OnInit(self):
        self.frame = MyFrame(None,"Gtruth")
        self.frame.Show(True)
        return True


class MainWindow(wx.ScrolledWindow):
    '''
    Displays the image and contains the NewPanel instances that form the
    graphical display of the bouding boxes.
    Handles calling the zooming functions of its members to zoom uniformly.
    '''
    def __init__(self, parent, id=-1):
        wx.ScrolledWindow.__init__(self, parent, size=(500,500))
        self.parent = parent

        # background when no image loaded
        parent.SetBackgroundColour('WHITE')

        # set-up scrolling
        self.SetScrollRate(20,20)

        # bind paint event so canvas will be redrawn
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        # bind mouse events
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnControlClick)

        # List of panels bounding the bars
        self.barpanels = []

        # List of panels bounding the staves
        self.staffpanels = [] 

        # Initially no background image
        self.bmp = None

        # for zooming, start at original size
        self.userscale = (1.0,1.0)
        
        # the panel we are currently resizing
        self.curpanel = None

        # for storing the state of the mouse button
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
        for p in self.barpanels:
            dc.SetBrush(wx.Brush('WHITE',\
                    style=wx.BRUSHSTYLE_TRANSPARENT))
            dc.SetPen(wx.Pen('RED',\
                    width=3, style=wx.PENSTYLE_SOLID))
            dc.DrawRectangle(*p.GetBox())
        for p in self.staffpanels:
            dc.SetBrush(wx.Brush('WHITE',\
                    style=wx.BRUSHSTYLE_TRANSPARENT))
            dc.SetPen(wx.Pen('GREEN',\
                    width=3, style=wx.PENSTYLE_SOLID))
            dc.DrawRectangle(*p.GetBox())

    def Zoom(self, factor):
        '''
        Scales the bitmap and panels according to zoom
        '''
        if factor < 0:
            raise ValueError
        usx, usy = self.userscale
        self.userscale = (usx * factor, usy * factor)
        self.Refresh()

    def OnLeftDown(self, evt):
        '''
        Start drawing a rectangle.
        If shift is down, edit an old panel.
        '''

        if self.leftdown ==  False:

            if self.parent.rectmode == 'BAR':
                panels = self.barpanels
            elif self.parent.rectmode == 'STAFF':
                panels = self.staffpanels
            else:
                self.GetStatusBar().SetStatusText(\
                        "Unrecognized rectangle mode " + self.parent.rectmode)
                self.ReleaseMouse()
                return

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

                rects = sort_by_area(panels)

                self.curpanel = find_smallest_enclosing_rect(rects,\
                        (unscrolledevtx/self.userscale[0],\
                        unscrolledevty/self.userscale[1]))

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

                panels.append(Rect(self.leftdownorigx,\
                        self.leftdownorigy,0,0))

                self.curpanel = panels[-1]

            self.Refresh()
            self.ReleaseMouse()

    def OnControlClick(self, evt):
        '''
        Destroy the smallest rectangle beneath the mouse.
        '''

        if self.parent.rectmode == 'BAR':
            panels = self.barpanels
        elif self.parent.rectmode == 'STAFF':
            panels = self.staffpanels
        else:
            self.parent.GetStatusBar().SetStatusText(\
                    "Unrecognized rectangle mode " + self.parent.rectmode)
            return

        self.CaptureMouse()

        unscrolledevtx, unscrolledevty = \
            self.CalcUnscrolledPosition(evt.GetPosition())

        x0, y0 = (unscrolledevtx/self.userscale[0],\
                        unscrolledevty/self.userscale[1])

        rects = sort_by_area(panels)

        rect = find_smallest_enclosing_rect(rects, (x0,y0))

        if rect == None:
            self.CaptureMouse()
            return

        panels.remove(rect)

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
    '''All the standard application stuff is dealt with here like the file
    menu.'''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)

        ### sw-canvas-funtions doesn't include rectmode yet
        # 'BAR' mode can be set to set the mouse to draw rectangles for the bars
        # 'STAFF' can be set to set the mouse to draw raectangels for the staves
        self.rectmode = 'BAR' # default start in 'BAR' mode
        
        # Set-up menus
        filemenu = wx.Menu()
        helpmenu = wx.Menu()

        # get information of program
        helpmenu.Append(wx.ID_ABOUT, "&About\tF1", "Show about dialog")

        # exit program
        filemenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit the example")
        
        # open a picture
        filemenu.Append(wx.ID_OPEN, "O&pen\tAlt-O", "Open a picture for "\
                                        +"annotating")

        # clear the rectangles
        filemenu.Append(wx.ID_CLEAR, "C&lear", "Clear all rectangles")

        # save the rectangle state
        filemenu.Append(wx.ID_SAVE, "S&ave\tShift-Alt-S",\
                "Save rectangle data")

        # load some rectangles (for testing usually)
        filemenu.Append(ID_LOAD_BOXES, "L&oad \tAlt-L",\
                "Load some rectangles")

        # entries for zooming in and out
        filemenu.Append(ID_ZOOM_IN, "Zoom In\tAlt-+",\
                "Zoom in the window")
        filemenu.Append(ID_ZOOM_OUT, "Zoom Out\tAlt--",\
                "Zoom out the window")

        # get help on using the program
        helpmenu.Append(ID_HELP_DLG, "H&elp \tAlt-H",\
                "How to use this program")

        # Directly create a wx.MenuItem because we want to change the string
        # displayed depending on the mode we are in.
        # Default is to begin in bar mode
        self.rectmodemenuitem = wx.MenuItem(filemenu,id=ID_TOGGLE_RECT_MODE,\
                text="Staff mode\tAlt-M",\
                help="Toggle the box colour and type (bar or staff)")
        filemenu.AppendItem(self.rectmodemenuitem)

        # put menus in menu bar
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        menubar.Append(helpmenu, "&Help")
        self.SetMenuBar(menubar)

        # bind menu methods
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnClearRect, id=wx.ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.OnLoadRects, id=ID_LOAD_BOXES)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=ID_HELP_DLG)
        self.Bind(wx.EVT_MENU, self.OnRectModeTog, id=ID_TOGGLE_RECT_MODE)
        # bind zoom in and zoom out methods
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=ID_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=ID_ZOOM_OUT)

        # how zoomed in we are 
        self.zoomfactor = 1.0

        # show staus messages
        self.CreateStatusBar()

        # name of currently open picture file
        self.curpicfilename = ''

        # child window that is the window containing all the elements
        self.scrolledwin = MainWindow(self)

        # initialize gamera so it works
        gamera.core.init_gamera()

        # place to store gamera image proxy for getting dpi basically
        self.image = None

    def Zoom(self, factor):
        try:
            self.scrolledwin.Zoom(factor)
        except ValueError:
            # This really shouldn't happen with "geometric" zooming (multiplying
            # by a factor)
            print 'Cannot zoom beyond limit.'

    def OnZoomIn(self, evt):
        self.Zoom(1.1)

    def OnZoomOut(self, evt):
        self.Zoom(0.9)
    ###

    def OnRectModeTog(self, event):
        if self.rectmode == 'BAR':
            self.rectmode = 'STAFF'
            self.rectmodemenuitem.SetText("Bar mode\tAlt-M")
        else:
            self.rectmode = 'BAR'
            self.rectmodemenuitem.SetText("Staff mode\tAlt-M")

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self,\
                "This is the ground truth evaluation system for the "
                +"barlinefinder.\n\n"
                +"Created by Nicholas Esterer Februrary 2013\n"
                +"Contact: nicholas.esterer@gmail.com",\
                caption="About Gtruth")
        dlg.ShowModal()

    def OnHelp(self, event):
        dlg = wx.MessageDialog(self, helpmess,\
                caption="How to use Gtruth",\
                style=(wx.OK|wx.ICON_QUESTION))
        dlg.ShowModal()
    
    def OnExit(self, event):
        print "Good-bye now!"
        self.Close()

    def OnOpen(self, event):

        fdlg = wx.FileDialog(self)

        if fdlg.ShowModal() == wx.ID_OK:

            fname = fdlg.GetFilename()

            # Do we add support for other image types?
            if not fname.endswith('.tiff') and not (fname.endswith('.tif')):
                self.GetStatusBar().SetStatusText(\
                    "Must be a TIFF file.") 

                return

            # Load gamera image to run property methods later
            self.image = gamera.core.load_image(fdlg.GetPath())

            # a string to print status to
            statusstr = "File loaded: %s, resolution %d dpi" % \
                    (fdlg.GetPath(), self.image.resolution)

            # Do we add support for other image types?
            bmp = wx.Bitmap(fdlg.GetPath(), wx.BITMAP_TYPE_TIF)

            self.curpicfilename = fdlg.GetFilename()

            self.scrolledwin.maxWidth = bmp.GetWidth()

            self.scrolledwin.maxHeight = bmp.GetHeight()

            self.scrolledwin.SetVirtualSize((self.scrolledwin.maxWidth,\
                                            self.scrolledwin.maxHeight))
            self.scrolledwin.bmp = bmp

            if fname.endswith('.tiff'):

                self.curpicfilename = fname[:fname.rfind('.tiff')]

            elif fname.endswith('.tif'):

                self.curpicfilename = fname[:fname.rfind('tif')]

            else:

                self.curpicfilename = fname

            self.scrolledwin.Refresh()

    def OnSave(self, event):

        fdlg = wx.FileDialog(self,\
                style = (wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT))

        # Suggest a filename based on the image name
        fdlg.SetFilename(self.curpicfilename + "_boxes.mei")

        xoffset, yoffset = self.scrolledwin.CalcUnscrolledPosition(0,0)

        if fdlg.ShowModal() == wx.ID_OK:
            # Prepare arrays of the bar bounding boxes and the staff bounding
            # boxes
            # staff bounding boxes
            # according to a print out of the data in meicreate these are given
            # as a list of lists, the list contiains:
            # [staffnumber, topcorner x, topcorner y, bottom corner x, bottom
            # corner y]

            staff_bb = []

            idx = 1 # TODO: Maybe we have to number the boxes differently
            for rect in self.scrolledwin.staffpanels:

                xtop, ytop = rect.GetPosition()

                xbot, ybot = rect.GetSize()

                staff_bb.append([idx, xtop, ytop,\
                        xbot, ybot])

                idx = idx + 1

            # bar bounding boxes
            # according to a print out of the data in meicreate these are given
            # as a list of tuples, the list contiains:
            # (staffnumber, topcorner x, topcorner y, bottom corner x, bottom
            # corner y)
            bar_bb = []

            idx = 1 # TODO: Maybe we have to number the boxes differently

            for rect in self.scrolledwin.barpanels:

                xtop, ytop = rect.GetPosition()
                
                xbot, ybot = rect.GetSize()

                bar_bb.append((idx, xtop, ytop,\
                        xbot, ybot))

                idx = idx + 1

            barconverter = gtruth_meicreate.GroundTruthBarlineDataConverter(\
                    staff_bb, bar_bb, True)

            if self.scrolledwin.bmp != None:

                width = self.scrolledwin.bmp.GetWidth()

                height = self.scrolledwin.bmp.GetHeight()

            if self.image == None:
                self.GetStatusBar().SetStatusText("No image file loaded, saving\
                        aborted.")
                return
            else:
                dpi = self.image.resolution

            barconverter.bardata_to_mei(str(self.curpicfilename),\
                    width, height, dpi) # using default dpi

            barconverter.output_mei(str(fdlg.GetPath()))

            self.GetStatusBar().SetStatusText("Saved to: " + fdlg.GetPath())

    def OnLoadRects(self, event):
        '''
        This method is depreciated.
        fdlg = wx.FileDialog(self)
        if fdlg.ShowModal() == wx.ID_OK:
            print "File loaded: " + fdlg.GetPath()
            f = open(str(fdlg.GetPath()),"r")
            rectstr = ''
            while True:
                rectstr = f.readline()
                if len(rectstr) == 0:
                    break;
                pos, size  = eval(rectstr.strip())
                self.scrolledwin.panels.append(\
                        NewPanel(self.scrolledwin,\
                        self.scrolledwin.CalcScrolledPosition(pos),\
                        size))
            f.close()
        '''
        pass

    def OnClearRect(self, event):
        if self.rectmode == 'BAR':
            panels = self.scrolledwin.barpanels
        elif self.rectmode == 'STAFF':
            panels = self.scrolledwin.staffpanels
        else:
            self.GetStatusBar().SetStatusText(\
                    "Unrecognized rectangle mode" + self.parent.rectmode)
            return
        while len(panels) > 0:
            rect = panels.pop()
            del(rect)

app = MyApp()
app.MainLoop()
