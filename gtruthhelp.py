'''
The text editor for barline ground-truth.
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
