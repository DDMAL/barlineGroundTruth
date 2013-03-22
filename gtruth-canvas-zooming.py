#!/usr/bin/env python

import wx
import sys
import gtruth_meicreate
from   gtruth_zoom import ZoomerMover
from gtruth_sorts import *

# For image preprocessing
import gamera.core
from gamera.toolkits import musicstaves, lyric_extraction, border_removal
from gamera.classify import BoundingBoxGroupingFunction, ShapedGroupingFunction
from gamera import classify
from gamera import knn
from gtruthrect import *
from gtruthtextedit import *
from gtruthhelp import GtruthHelpFrame, helpmess
import os.path
import tempfile

# For loading meifiles
from pymei import MeiDocument, MeiElement, XmlImport

'''Must append path to meicreate.py to PYTHONPATH environment variable unless
this is run in the same directory as it. '''

# for debugging
__GTRUTH_DEBUG__ = True

# custom event ids
ID_LOAD_BOXES       = wx.ID_HIGHEST + 1
ID_HELP_DLG         = wx.ID_HIGHEST + 2
ID_TOGGLE_RECT_MODE = wx.ID_HIGHEST + 3
ID_ZOOM_IN          = wx.ID_HIGHEST + 4
ID_ZOOM_OUT         = wx.ID_HIGHEST + 5
ID_MINBOX_INC       = wx.ID_HIGHEST + 6
ID_MINBOX_DEC       = wx.ID_HIGHEST + 7

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

        # To prevent the user from making minature boxes that cannot be found to
        # be deleted we impose a minimum box size. If this turns out to be
        # bothersome, the user may increase or decrease the minimum box size
        self.minboxsize = 20 # the size of the x and y dimensions

        self.Show(True)
        self.Refresh()

    def _EnforceMinPanelSize(self, size):
        # set size conditional on the minimum box size
        if self.curpanel == None:
            return
        sizex, sizey = size
        if (sizex < (self.minboxsize/self.userscale[0])) | (sizey <
                (self.minboxsize/self.userscale[1])):
            self.curpanel.SetSize((self.minboxsize/self.userscale[0],\
                     self.minboxsize/self.userscale[1]))
        else:
            self.curpanel.SetSize(size)

    def _HandleBoxDrawingMotion(self, x0, y0):
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
        return (pos,size)

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
                    width=3.0/self.userscale[0], style=wx.PENSTYLE_SOLID))
            dc.DrawRectangle(*p.GetBox())
        for p in self.staffpanels:
            dc.SetBrush(wx.Brush('WHITE',\
                    style=wx.BRUSHSTYLE_TRANSPARENT))
            dc.SetPen(wx.Pen('GREEN',\
                    width=3.0/self.userscale[0], style=wx.PENSTYLE_SOLID))
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

            vsx, vsy = self.GetViewStart()

            spux, spuy = self.GetScrollPixelsPerUnit()

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
                        self.leftdownorigy,0,0,-1))

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
            self.ReleaseMouse()
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

            pos, size = self._HandleBoxDrawingMotion(x0, y0)

            # set size conditional on the minimum box size
            self._EnforceMinPanelSize(size)

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

            pos, size = self._HandleBoxDrawingMotion(x0, y0)

            self.leftdown = False
            
            # set size conditional on the minimum allowed size
            self._EnforceMinPanelSize(size)

            self.curpanel.SetPosition(pos)
            self.curpanel = None
            self.Refresh()
            self.ReleaseMouse()
    
class MyFrame(wx.Frame):
    '''All the standard application stuff is dealt with here like the file
    menu.'''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)

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

        # entries for increasing and decreasing the minimum box size
        filemenu.Append(ID_MINBOX_INC, "Increase minimum\tAlt->",\
                "Increase minimum box size")
        # clear the rectangles
        filemenu.Append(wx.ID_CLEAR, "C&lear", "Clear all rectangles")
        filemenu.Append(ID_MINBOX_DEC, "Decrease minimum\tAlt-<",\
                "Decrease minimum box size")

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

        # bind minbox inc and dec methods
        self.Bind(wx.EVT_MENU, self.OnMinboxInc, id=ID_MINBOX_INC)
        self.Bind(wx.EVT_MENU, self.OnMinboxDec, id=ID_MINBOX_DEC)

        # how zoomed in we are 
        self.zoomfactor = 1.0

        # show staus messages
        self.CreateStatusBar()

        # name of currently open picture file
        self.curpicfilename = ''

        # child window that is the window containing all the elements
        self.scrolledwin = MainWindow(self)

        # child window containing the text box
        self.textwin = GtruthTextFrame(self, pos=(100,100), size=(200,400),\
            title="Gtruth Text Editor")

        # help frame that will display help when requested
        self.helpwin = None

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

    def OnMinboxInc(self, evt):
        '''
        Increase minimum box size.
        '''
        self.scrolledwin.minboxsize = self.scrolledwin.minboxsize + 1
        self.GetStatusBar().SetStatusText("Increased minimum box size to %d." %\
                self.scrolledwin.minboxsize)

    def OnMinboxDec(self, evt):
        '''
        Decrease minimum box size.
        '''
        if self.scrolledwin.minboxsize > 1:
            self.scrolledwin.minboxsize = self.scrolledwin.minboxsize - 1
            self.GetStatusBar().SetStatusText("Decreased minimum box size to %d." %\
                self.scrolledwin.minboxsize)
            return
        self.GetStatusBar().SetStatusText(("Minimum box size at minimum: %d, "\
                + "cannot decrease.") %\
                self.scrolledwin.minboxsize)


    def OnZoomIn(self, evt):
        self.Zoom(1.1)

    def OnZoomOut(self, evt):
        self.Zoom(0.9)

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
        self.helpwin = GtruthHelpFrame(self, pos=(200,100),\
            text=helpmess)
    
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

            # make image greyscale
            self.image = self.image.to_greyscale()

            # binarize image
            self.image = self.image.to_onebit()

            # correct the rotation of the image
            self.image = self.image.correct_rotation(0)

            # TODO: border removal could happen here too

            # get an image path that doesn't end in .tiff or .tif
            fname = fdlg.GetPath()

            if fname.endswith('.tiff'):

                self.curpicfilename = fname[:fname.rfind('.tiff')]

            elif fname.endswith('.tif'):

                self.curpicfilename = fname[:fname.rfind('tif')]

            else:

                self.curpicfilename = fname

            print "Current picture file name:", self.curpicfilename

            # path to preprocessed image version
            tempimage = tempfile.NamedTemporaryFile()
            ppimagepath = tempimage.name

            self.image.save_tiff(ppimagepath)

            # Load the preprocessed image's pixels
            bmp = wx.Bitmap(ppimagepath, wx.BITMAP_TYPE_TIF)

            # a string to print status to
            statusstr = "File loaded: %s, resolution %d dpi" % \
                    (ppimagepath, self.image.resolution)

            self.scrolledwin.maxWidth = bmp.GetWidth()

            self.scrolledwin.maxHeight = bmp.GetHeight()

            self.scrolledwin.SetVirtualSize((self.scrolledwin.maxWidth,\
                                            self.scrolledwin.maxHeight))
            self.scrolledwin.bmp = bmp

            self.scrolledwin.Refresh()

    def OnSave(self, event):

        fdlg = wx.FileDialog(self,\
                style = (wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT))

        # Suggest a filename based on the image name
        fdlg.SetFilename(os.path.basename(self.curpicfilename) + "_boxes.mei")

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

            idx = 1 # TODO: Maybe we have to number the staves differently
            for rect in self.scrolledwin.staffpanels:

                # Find the rectangles this rectangle bounds
                children = rect.GetRectsInBounds(self.scrolledwin.barpanels)

                # Find rectangle that tightly bounds the rectangles inside of
                # it.

                try:
                    brect = get_bounding_rect(children)
                except ValueError:
                    print "Tried to get bounding rectangle of empty list."
                    continue

                # Set its children to the bounded rects
                
                brect.SetChildren(children)
                brect.SetNumber(idx) # Identify the staff with a number, not
                                     # really important right now

                # We don't use FindChildren because I'm worried some children
                # might be missing after resizing (this is a stupid worry) but
                # also due to the order of how this saving is carried out

                # Then save this rect

                xtop, ytop = brect.GetPosition()

                xbot, ybot = brect.GetSize()

                staff_bb.append(brect)

                idx = idx + 1

            # Sort the staves by upper left hand y coordinate and their children
            # by upper left hand x coordinate so that they may be accurately
            # numbered
            staff_bb.sort(key=lambda c: c.pos[1])
            idx = 1
            for rect in staff_bb:
                rect.children.sort(key=lambda c: c.pos[0])
                # assuming no bars belonging to multiple staves, they may now be
                # numbered
                try:
                    for c in rect.children:
                        c.SetNumber(idx)
                        idx = idx + 1
                except TypeError:
                    self.GetStatusBar().SetStatusText("Warning: a staff "\
                            + "contains no bars.")
                    pass

            for b in self.scrolledwin.barpanels:
                if b.number == -1:
                    self.GetStatusBar().SetStatusText("Warning: a bar was not "\
                                                        + "numbered.")
                    warningdlg = wx.MessageDialog(self,\
                            message="Warning: a bar was not numbered. Would "\
                            + "you like to go back to correct this?",\
                            caption="A bar was not numbered.",\
                            style=(wx.YES_NO))
                    if warningdlg.ShowModal() == wx.ID_YES:
                        self.GetStatusBar().SetStatusText('Saving aborted.')
                        return


            # bar bounding boxes
            # according to a print out of the data in meicreate these are given
            # as a list of tuples, the list contiains:
            # (staffnumber, topcorner x, topcorner y, bottom corner x, bottom
            # corner y)

            barconverter = gtruth_meicreate.GroundTruthBarlineDataConverter(\
                    staff_bb, self.scrolledwin.barpanels, True)

            if self.scrolledwin.bmp != None:

                width = self.scrolledwin.bmp.GetWidth()

                height = self.scrolledwin.bmp.GetHeight()

            if self.image == None:
                self.GetStatusBar().SetStatusText('No image file loaded, '\
                        + 'saving aborted.')
                return
            else:
                dpi = self.image.resolution

            barconverter.bardata_to_mei(str(self.curpicfilename),\
                    width, height, dpi) # using default dpi

            barconverter.output_mei(str(fdlg.GetPath()))
            fname = fdlg.GetPath()
            fname = fname[:fname.rfind('.mei')] + ".txt"

            self.textwin.SaveText(fname)
            self.GetStatusBar().SetStatusText(("MEI saved to: %s. " +\
                    "Text saved to: %s") % (fdlg.GetPath(), fname))

    def OnLoadRects(self, event):
        '''
        Loads rectangles from an mei file.
        Only loads bar boxes and not staff boxes yet.
        '''

        fdlg = wx.FileDialog(self)

        if fdlg.ShowModal() == wx.ID_OK:
            
            print "File loaded: " + fdlg.GetPath()

            meidoc = XmlImport.documentFromFile(str(fdlg.GetPath()))

            # get all the measure elements
            measures = meidoc.getElementsByName('measure')

            # the measures have their coordinates stored in zones
            zones = meidoc.getElementsByName('zone')

            for m in measures:

                # the id of the zone that has the coordinates is stored in 'facs'
                facs = m.getAttribute('facs')

                print facs.getName(), facs.getValue()

                # there's a # sign preceding the id stored in the facs
                # attribute, remove it
                zone = meidoc.getElementById(facs.getValue()[1:])

                # the coordinates stored in zone
                ulx = zone.getAttribute('ulx').getValue()
                uly = zone.getAttribute('uly').getValue()
                lrx = zone.getAttribute('lrx').getValue()
                lry = zone.getAttribute('lry').getValue()

                print ulx, uly, lrx, lry

                # make a new panel
                self.scrolledwin.barpanels.append(\
                        Rect(int(ulx), int(uly), int(lrx), int(lry)))

            self.scrolledwin.Refresh()


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
        self.scrolledwin.Refresh()

app = MyApp()
app.MainLoop()
