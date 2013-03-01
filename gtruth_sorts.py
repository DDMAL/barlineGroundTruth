
def sort_by_area(shapes):
    '''
    Returns the shapes sorted by increasing area
    '''
    return sorted(shapes, key=lambda shape:shape.GetArea())

def find_smallest_enclosing_rect(rects, point):
    '''
    Finds the smallest rectange in the list of rects that encloses
    the point. Rects must be sorted by increasing area, point is a 
    tuple like (2,3).
    '''
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


