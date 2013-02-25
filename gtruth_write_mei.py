#!/usr/bin/env python

import wx
import meicreate

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

ID_LOAD_BOXES = wx.ID_HIGHEST + 1
ID_HELP_DLG   = wx.ID_HIGHEST + 2
ID_TOGGLE_RECT_MODE = wx.ID_HIGHEST + 3

def sort_by_area(shapes):
    '''Returns the shapes sorted by increasing area'''
    return sorted(shapes, key=lambda shape:shape.GetArea())

def find_smallest_enclosing_rect(rects, point):
    '''Finds the smallest rectange in the list of rects that encloses
    the point. Rects must be sorted by increasing area, point is a 
    tuple like (2,3).'''
    x, y = point
    if(len(rects) < 1):
        return None
    currect = None
    for rect in reversed(rects):
        wx, wy = rect.GetPosition()
        ww, wh = rect.GetSize()
        if (x >= wx)\
            & (y >= wy)\
            & (x <= (wx + ww))\
            & (y <= (wy + wh)):
            currect = rect
    return currect

class NewPanel(wx.Panel):
    '''
    The NewPanel class represents the bounding boxes that are shown on the
    display.
    '''
    def __init__(self, parent, pos, size=(0,0), bordercolour='RED'):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos=pos, size=size,\
            style=  (wx.BORDER_NONE))
        self.bordercolour = bordercolour
        self.Enable(False)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnControlClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Show(True)
        self.Refresh()

    def OnPaint(self, evt):
        '''Called by the OS to refresh drawing. Draws the coloured border.'''
        dc = wx.PaintDC(self)
        posx, posy = self.GetPosition()
        sizex, sizey = self.GetSize()
        dc.SetBrush(wx.Brush('WHITE',style=wx.BRUSHSTYLE_TRANSPARENT))
        dc.SetPen(wx.Pen(self.bordercolour, width=3, style=wx.PENSTYLE_SOLID))
        dc.DrawRectangle(0, 0, sizex, sizey)

    
    def GetArea(self):
        w, h = self.GetSize()
        return w * h

    def OnLeftUp(self, evt):
        x, y = self.GetPosition()
        evt.SetX(evt.GetX() + x)
        evt.SetY(evt.GetY() + y)
        self.GetParent().ProcessEvent(evt)
    
    def OnMouseMove(self, evt):
        x, y = self.GetPosition()
        evt.SetX(evt.GetX() + x)
        evt.SetY(evt.GetY() + y)
        self.GetParent().ProcessEvent(evt)

    def OnLeftDown(self, evt):
        x, y = self.GetPosition()
        evt.SetX(evt.GetX() + x)
        evt.SetY(evt.GetY() + y)
        self.GetParent().ProcessEvent(evt)

    def OnControlClick(self, evt):
        x, y = self.GetPosition()
        evt.SetX(evt.GetX() + x)
        evt.SetY(evt.GetY() + y)
        self.GetParent().ProcessEvent(evt)

class MyApp(wx.App):
    '''The main app that contains all of the child windows.'''
    def OnInit(self):
        self.frame = MyFrame(None,"Gtruth")
        self.frame.Show(True)
        return True

class MainWindow(wx.ScrolledWindow):
    '''Displays the image and contains the NewPanel instances that form the
    graphical display of the bouding boxes.'''
    def __init__(self, parent, id=-1):
        wx.ScrolledWindow.__init__(self, parent, size=(500,500))
        self.parent = parent
        parent.SetBackgroundColour('WHITE')
        self.SetScrollRate(20,20)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnControlClick)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.leftdown = False
        self.x0 = 0
        self.y0 = 0
        self.barpanels = [] # List of panels bounding the bars
        self.staffpanels = [] # List of panels bounding the staves
        self.curpanel = None # The panel we are currently resizing
        # For background image
        self.bmp = None
        self.Show(True)
        self.Refresh()

#    def OnScroll(self, event):

    def OnPaint(self, event):
        '''Called by the OS to refresh drawing.'''
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        if self.bmp != None:
            dc.DrawBitmap(self.bmp,0,0,True)
    
    def OnLeftDown(self, evt):
            '''Start making a new panel on a left-click. If shift is down, edit
            an old panel.'''
            if self.parent.rectmode == 'BAR':
                panels = self.barpanels
                colour = 'RED'
            elif self.parent.rectmode == 'STAFF':
                panels = self.staffpanels
                colour = 'GREEN'
            else:
                self.parent.GetStatusBar().SetStatusText(\
                        "Unrecognized rectangle mode" + self.parent.rectmode)
                self.ReleaseMouse()
                return
            self.CaptureMouse()
            dc = wx.WindowDC(self)
            self.leftdown = True 
            if evt.ShiftDown():
                rects = sort_by_area(panels)
                self.curpanel = find_smallest_enclosing_rect(rects,\
                        evt.GetPosition())
                if self.curpanel == None:
                    self.leftdown = False
                else:
                    self.x0, self.y0 = self.curpanel.GetPosition()
            else:
                self.x0, self.y0 = evt.GetPosition()
                panels.append(NewPanel(self,pos=(self.x0,self.y0),\
                        bordercolour=colour))
                self.curpanel = panels[-1]
            self.ReleaseMouse()

    def OnControlClick(self, evt):
        '''Destroy the smallest rectangle beneath the mouse.'''
        if self.parent.rectmode == 'BAR':
            panels = self.barpanels
        elif self.parent.rectmode == 'STAFF':
            panels = self.staffpanels
        else:
            self.parent.GetStatusBar().SetStatusText(\
                    "Unrecognized rectangle mode " + self.parent.rectmode)
            return
        self.CaptureMouse()
        rects = sort_by_area(panels)
        rect = find_smallest_enclosing_rect(rects, evt.GetPosition())
        if rect == None:
            self.parent.GetStatusBar().SetStatusText(\
                    "Nothing beneath mouse at " + str(evt.GetPosition()))
            self.ReleaseMouse()
            return
        rect.SetBackgroundColour(wx.Colour(0,0,255))
        dc = wx.WindowDC(self)
        self.parent.GetStatusBar().SetStatusText(\
            "Position of Click " + str(evt.GetPosition()))
        self.parent.GetStatusBar().SetStatusText(\
            "Position of rectangle " + str(rect.GetPosition()))
        panels.remove(rect)
        rect.Destroy()
        self.ReleaseMouse()

    def OnMouseMove(self, evt):
        '''Resize the rectange as we're drawing it, if we're drawing it.'''
        if self.leftdown == True:
            if self.parent.rectmode == 'BAR':
                panels = self.barpanels
            elif self.parent.rectmode == 'STAFF':
                panels = self.staffpanels
            else:
                self.parent.GetStatusBar().SetStatusText(\
                    "Unrecognized rectangle mode" + self.parent.rectmode)
                self.ReleaseMouse()
                return
            self.CaptureMouse()
            dc = wx.WindowDC(self)
            x1, y1 = evt.GetPosition()
            # Some logic to handle all start and end drawing motions
            if x1 > self.x0:
                if y1 > self.y0:
                    pos = (self.x0, self.y0)
                    size = (x1 - self.x0, y1 - self.y0)
                else:
                    pos = (self.x0, y1)
                    size = (x1 - self.x0, self.y0 - y1)
            else:
                if y1 > self.y0:
                    pos = (x1,self.y0)
                    size = (self.x0-x1,y1-self.y0)
                else:
                    pos = (x1, y1)
                    size = (self.x0 - x1, self.y0 - y1)
            if(len(panels) > 0):
                self.curpanel.SetSize(size)
                self.curpanel.SetPosition(pos)
                self.curpanel.Show(True)
            self.parent.GetStatusBar().SetStatusText(\
                    "mouse moved to " + str((x1,y1)))
            self.ReleaseMouse()

    
    def OnLeftUp(self, evt):
        '''When left mouse button released, you have a box.'''
        if self.leftdown == True:
            self.CaptureMouse()
            dc = wx.WindowDC(self)
            x1, y1 = evt.GetPosition()
            # The same drawing logic.
            if x1 > self.x0:
                if y1 > self.y0:
                    pos = (self.x0, self.y0)
                    size = (x1 - self.x0, y1 - self.y0)
                else:
                    pos = (self.x0, y1)
                    size = (x1 - self.x0, self.y0 - y1)
            else:
                if y1 > self.y0:
                    pos = (x1,self.y0)
                    size = (self.x0-x1,y1-self.y0)
                else:
                    pos = (x1, y1)
                    size = (self.x0 - x1, self.y0 - y1)
            self.parent.GetStatusBar().SetStatusText(\
                    "mouse up at " + str((x1,y1)))
            self.leftdown = False
            self.ReleaseMouse()
        self.curpanel = None
    
class MyFrame(wx.Frame):
    '''All the standard application stuff is dealt with here like the file
    menu.'''
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title)
        # 'BAR' mode can be set to set the mouse to draw rectangles for the bars
        # 'STAFF' can be set to set the mouse to draw raectangels for the staves
        self.rectmode = 'BAR' # default start in 'BAR' mode
        filemenu = wx.Menu()
        helpmenu = wx.Menu()
        helpmenu.Append(wx.ID_ABOUT, "&About\tF1", "Show about dialog")
        filemenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit the example")
        filemenu.Append(wx.ID_OPEN, "O&pen\tAlt-O", "Open a picture for "\
                                        +"annotating")
        filemenu.Append(wx.ID_CLEAR, "C&lear", "Clear all rectangles")
        filemenu.Append(wx.ID_SAVE, "S&ave\tShift-Alt-S",\
                "Save rectangle data")
        filemenu.Append(ID_LOAD_BOXES, "L&oad \tAlt-L",\
                "Load some rectangles")
        helpmenu.Append(ID_HELP_DLG, "H&elp \tAlt-H",\
                "How to use this program")
        # Directly create a wx.MenuItem because we want to change the string
        # displayed depending on the mode we are in.
        # Default is to begin in bar mode
        self.rectmodemenuitem = wx.MenuItem(filemenu,id=ID_TOGGLE_RECT_MODE,\
                text="Staff mode\tAlt-M",\
                help="Toggle the box colour and type (bar or staff)")
        filemenu.AppendItem(self.rectmodemenuitem)
        menubar = wx.MenuBar()
        menubar.Append(filemenu, "&File")
        menubar.Append(helpmenu, "&Help")
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnClearRect, id=wx.ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.OnLoadRects, id=ID_LOAD_BOXES)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=ID_HELP_DLG)
        self.Bind(wx.EVT_MENU, self.OnRectModeTog, id=ID_TOGGLE_RECT_MODE)
        self.CreateStatusBar()
        self.bmp = None
        self.scrolledwin = MainWindow(self)
        self.curpicfilename = ''

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
            if not fname.endswith('.tiff') and not (fname.endswith('.tif')):
                self.GetStatusBar().SetStatusText(\
                    "Must be a TIFF file.")
                return
            self.GetStatusBar().SetStatusText("File loaded: " + fdlg.GetPath())
            # Do we add support for other image types?
            bmp = wx.BitmapFromImage(\
                    wx.Image(fdlg.GetPath(), wx.BITMAP_TYPE_TIF))
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
                staff_bb.append([idx, xtop+xoffset, ytop+yoffset,\
                        xbot+xoffset, ybot+yoffset])
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
                bar_bb.append((idx, xtop+xoffset, ytop+yoffset,\
                        xbot+xoffset, ybot+yoffset))
                idx = idx + 1
            barconverter = meicreate.BarlineDataConverter(staff_bb, bar_bb,
                    True)
            # I don't have an sg_hint, nor image_dpi
            # I am passing "()" and 72 respectively, I do not know of any
            # repercussions
            if self.scrolledwin.bmp != None:
                width = self.scrolledwin.bmp.GetWidth()
                height = self.scrolledwin.bmp.GetHeight()
            barconverter.bardata_to_mei("()", str(self.curpicfilename),\
                    width, height, 72)
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
            rect.Destroy()

app = MyApp()
app.MainLoop()
