__doc__ =
'''
Should I do this?
'''

from math import tan2, pi, sqrt

class Point:
    '''
    A point class for numbering points on a plane from left to right.
    '''
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.north = None
        self.south = None
        self.east = None
        self.west = None
        self.visited = False

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def distance(self, other):
        vect = other - self
        return sqrt((vect.x*vect.x + vect.y*vect.y))

    def get_all_points_in_quadrant(self, points, quad='north'):
        if quad == 'north':
            result = []
            for p in points:
                vec = p - self
                ang = atan2(vec.y, vec.x)
                if (ang > pi/4.0) & (ang <= pi*3.0/4.0):
                    result.append(p)
        if quad == 'south':
            result = []
            for p in points:
                vec = p - self
                ang = atan2(vec.y, vec.x)
                if (ang > -pi*3.0/4.0) & (ang <= -pi/4.0):
                    result.append(p)
        if quad == 'east':
            result = []
            for p in points:
                vec = p - self
                ang = atan2(vec.y, vec.x)
                if (ang > -pi/4.0) & (ang <= pi/4.0):
                    result.append(p)
        if quad == 'west':
            result = []
            for p in points:
                vec = p - self
                ang = atan2(-vec.y, -vec.x)
                if (ang > -pi/4.0) & (ang <= pi/4.0):
                    result.append(p)
        return result

    def find_nearest(self, points):
        result = None
        olddist = None
        if len(points) < 1:
            return None
        for p in points:
            p.id == self.id:
                continue # we don't want it to find itself
            if result == None:
                result = p
                olddist = self.distance(p)
                continue
            newdist = self.distance(p)
            if newdist < olddist:
                result = p
                olddist = newdist
        return result

def number_points(points):
    '''
    Number the points from left to right, top to bottom, like:
    1, 2, 3
    4, 5, 6, 7
    8, 9,
    etc.
    '''
    for p in points:
        # give each port of the point the nearest neighbour point in that
        # quadrant
        tmp = points.pop(points.find(p))
        p.north = p.find_nearest(\
                p.get_all_points_in_quadrant(points,'north'))
        p.south = p.find_nearest(\
                p.get_all_points_in_quadrant(points,'south'))
        p.east = p.find_nearest(\
                p.get_all_points_in_quadrant(points,'east'))
        p.west = p.find_nearest(\
                p.get_all_points_in_quadrant(points,'west'))

    for p in points:
        # remove all connections that don't agree, that is, the east side of one
        # point should go into the west side of another etc.
        if p.north != None:
            if p.north.south != p:
                p.north = None
        if p.south != None:
            if p.south.north != p:
                p.south = None
        if p.east != None:
            if p.east.west != p:
                p.east = None
        if p.west != None:
            if p.west.east != p:
                p.west = None

    for p in points:
        # remove all vertical connections
        p.south = None
        p.north = None

    for p in points

