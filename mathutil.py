import math
import bisect

def sign(v):
    # v == 0: return  0
    # v > 0 : return  1
    # v < 0 : return -1
    return 0 if v == 0 else (1 if v >= 0 else -1)
  
def lerp(a,b,t):
    # linear interpolation between scalars a and b using t
    return (1-t)*a + t*b
    
def clamp(x,a,b):
    return min(max(x,a),b)
    
def step(a,t):
    return 0 if t < a else 1
    
def smoothstep(a,b,t):
    x = clamp((t-a)/(t-a),0,1)
    return x*x*(3-2*x)
    
def smootherstep(a,b,t):
    x = clamp((t-a)/(t-a),0,1)
    return x * x * x * (x * (x * 6 - 15) + 10)
    
def dot(v,q):
    return v[0]*q[0] + v[1]*q[1]

class ivec2(object):
    def __init__(self, x=0, y=0):
        self.x = int(x)
        self.y = int(y)

    def dot(self, q):
        # dot product
        return self.x*q.x + self.y*q.y

    def squaredLength(self):
        return self.dot(self)

    def length(self):
        return math.sqrt(self.squaredLength())

    def abs(self):
        return ivec2(abs(self.x),abs(self.y))

    def get(self, i):
        # get the i-th component
        return self.x if i == 0 else self.y

    def sign(self):
        # vector-form of the sign function
        return ivec2(sign(self.x), sign(self.y))
        
    def muls(self, scalar):
        return ivec2(self.x*scalar, self.y * scalar)
        
    def mulv(self, v):
        return ivec2(self.x*v.x, self.y * v.y)

    def normalized(self):
        # Return a unit vector based on this. return (0,0) if this vector is zero
        l = self.length()
        mul = 1.0/l if l > 0.0 else 1
        return (self.x*mul,self.y*mul) # don't return ivec2 because it will be zero! (it's integer vector)

    def __eq__(self,q):
        return self.x==q.x and self.y==q.y

    def __str__(self):
        return "({0},{1})".format(self.x, self.y)

    def __add__(self, other):
        x = self.x + other.x
        y = self.y + other.y
        return ivec2(x, y)
    def __sub__(self, other):
        x = self.x - other.x
        y = self.y - other.y
        return ivec2(x, y)
    def __hash__(self):
        return hash((self.x,self.y))

class SortedPoints(object):
    """
        Store a list of ivec2 points, sorted by euclidean length, like starting from the origin and going outwards on a spiral
        Also store the squared lengths for each of the sorted points, so that we can do efficient binary search
    """
    
    def __init__(self, maxLos):
        self.points = []
        for y in range(-maxLos,maxLos+1):
            for x in range(-maxLos,maxLos+1):
                self.points.append(ivec2(x,y))
        self.points.sort(key=lambda p: p.squaredLength())
        self.keys = [p.squaredLength() for p in self.points]
                
    def range(self, r_inner,r_outer):
        r_inner_squared = r_inner*r_inner
        r_outer_squared = r_outer*r_outer
        i0 = bisect.bisect_left( self.keys, r_inner_squared)
        i1 = bisect.bisect_right( self.keys, r_outer_squared)
        return self.points[i0:i1]
        # Slower version of above
        #return [x for x in self.points if x.squaredLength() >= r_inner_squared and x.squaredLength() <= r_outer_squared]
        
class Map2D(object):
    """
        2D array class, storing the data as a 1D list
    """
    def __init__(self, w,h, default_value = None):
        self.width = w
        self.height = h
        self.data = [default_value] * w*h
        
    def linear_index(self, point):
        return point.x+point.y*self.width
        
    def get(self, point ):
        assert( self.in_bounds(point))
        return self.data[ self.linear_index(point)]
        
    def set(self, point, value):
        assert( self.in_bounds(point))
        self.data[ self.linear_index(point)] = value
        
    def add(self, point, value):
        assert( self.in_bounds(point))
        self.data[ self.linear_index(point)] += value
        
    def in_bounds( self, point ):
        return point.x >= 0 and point.x < self.width and point.y >= 0 and point.y < self.height