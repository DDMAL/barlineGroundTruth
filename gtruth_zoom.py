'''
Abstract from this class to enable zooming.
'''

import abc

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

class ZoomerMover:
    '''
    A class that supports zooming objects that can be moved, granted the object
    that subclasses it has the methods:
    self.SetWidth()
    self.SetHeight()
    self.SetZoomedPosition()
    self.GetWidth()
    self.GetHeight()
    self.GetZoomedPosition()
    Sublassing this properly will allow you to zoom instances of the class
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
    def SetZoomedPosition(self, *args, **kwargs):
        pass
    @abc.abstractmethod
    def GetWidth(self, *args, **kwargs):
        pass
    @abc.abstractmethod
    def GetHeight(self, *args, **kwargs):
        pass
    @abc.abstractmethod
    def GetZoomedPosition(self, *args, **kwargs):
        pass

    def __init__(self):
        self.originalWidth = self.GetWidth()
        self.originalHeight = self.GetHeight()
        try:
            self.originalPosition = self.GetZoomedPosition()
        except NotImplementedError:
            self.originalPosition = (0,0)

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
            self.SetZoomedPosition((float(newposx) * factor, float(newposy) * factor))
        except NotImplementedError: 
            pass # if no set position function, just don't set it

