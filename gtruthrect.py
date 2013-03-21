'''
Rectangles that store position and hierarchy information (like what Rectangles
are inside of this rectangle) and have methods for finding rectangles with
certain properties.
'''

class Rect:
    '''
    Represents a rectangle.
    '''
    def __init__(self,posx,posy,szx,szy,num=-1):
        self.pos = (posx,posy)
        self.size = (szx,szy)
        self.children = []
        self.number = num

    def SetNumber(self,num):
        '''
        For identifying the rectangle with a number.
        '''
        self.number = num

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

    def GetRectsInBounds(self, rects):
        '''
        returns a list of all the rectangles whose corners are completely
        enclosed by this Rect.
        '''
        # Sort by upper left hand x coordinate
        rects.sort(key=lambda r: r.pos[0])
        # Remove all rects with upper left hand x coordinate less than this
        # one's
        rects = filter(lambda r: r.pos[0] >= self.pos[0], rects)
        # Then do the same with the lower right hand x coordinate
        rects = filter(lambda r: (r.pos[0] + r.size[0]) <= (self.pos[0]\
                + self.size[0]), rects)
        # Then do all of the above with the y coordinate
        rects.sort(key=lambda r: r.pos[1])
        rects = filter(lambda r: r.pos[1] >= self.pos[1], rects)
        rects = filter(lambda r: (r.pos[1] + r.size[1]) <= (self.pos[1]\
                + self.size[1]), rects)
        return rects

    def SetChildren(self, rects):
        self.children = rects

    def FindChildren(self, rects):
        '''
        Finds which rectangles in rects are within the bounds of this rectangle
        and store them as children. Note that if you do this and then move the
        rectangle, the children will remain... you have to clear them manually
        to aggree with reality (they may no longer be bounded by this rectangle)
        '''
        self.children = self.GetRectsInBounds(rects)

    def ClearChildren(self):
        self.children = []

def get_bounding_rect(rects):
    '''
    Return the rectangle that can fit all the rectangles within it.
    '''
    lowx = min(rects, key=lambda x: x.pos[0])
    lowy = min(rects, key=lambda x: x.pos[1])
    hix  = max(rects, key=lambda x: x.pos[0] + x.size[0])
    hiy  = max(rects, key=lambda x: x.pos[1] + x.size[1])
    return Rect(lowx.pos[0], lowy.pos[1], (hix.pos[0]+hix.size[0])-lowx.pos[0],\
            (hiy.pos[1]+hix.size[1])-lowy.pos[1])

