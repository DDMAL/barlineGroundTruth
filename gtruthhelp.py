'''
The text editor for barline ground-truth.
'''

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

There is a minimum box size that you are allowed to draw to keep \
you from saving some erroneous boxes. If you are finding that it \
be too small or large, it may be adjusted using Increase Minimum \
and Decrease Minimum.

You may get a warning message upon saving that some measures have \
not been numbered. This is most likely because a measure is not \
inside a staff bounding box. You have the option of going back \
and ensuring all measure boxes are enclosed in staff boxes, which \
you must do to save an accurate MEI file in the end.

The text box is available for making annotations. Upon saving, its \
contents will be saved to the file-path specified for the MEI file \
but ending in .txt.

WARNING: If you scroll while drawing a box it will mess up the top \
corner coordinates. If you would like to draw a box larger than the \
screen, simply draw the box as large as you can, let go of the \
mouse button, scroll the window and then shift-click on the box to \
resize it.
'''

import wx

class GtruthHelpFrame(wx.Frame):
    '''
    Frame containing the textbox.
    '''
    def __init__(self, parent, pos=(100,100), size=(400,600),\
            title="Ground Truth Help",text="Good morning world!"):
        wx.Frame.__init__(self, parent, pos=pos, title=title, size=size)
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.control.Replace(0,len(text),text)
        self.control.SetEditable(False)
        self.Show(True)

    def SaveText(self, filename):
        self.control.SaveFile(filename,wx.TEXT_TYPE_ANY)
