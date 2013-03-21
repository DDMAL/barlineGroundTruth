'''
The text editor for barline ground-truth.
'''

import wx

class GtruthTextFrame(wx.Frame):
    '''
    Frame containing the textbox.
    '''
    def __init__(self, parent, pos=(100,100), size=(200,200),\
            title="Ground Truth Text Frame"):
        wx.Frame.__init__(self, parent, pos=pos, title=title, size=size)
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.Show(True)

    def SaveText(self, filename):
        self.control.SaveFile(filename,wx.TEXT_TYPE_ANY)
