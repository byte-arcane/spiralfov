import math
from timeit import default_timer as timer
from enum import IntEnum
from mathutil import *

# Smaller value (always in [0,1]) leads to less decay
DECAY_PER_TILE_PERCENT = 0.9 # e.g. Visibility reduces to 90% from a tile to the next

"""
    TODOs:
        each point reads from 2. So, change so I don't write to future objects
        
"""

def fov( viewerPos, losRadius, visibilityMap, onFovSetCallback = None):
    """
    Calculate the field-of-vision map (0: can't see, 1: see maximum, and anything in between)
    onFovSetCallback: callback to mark all the cells we've visited (parameters: position and visibility value)
    """
    
    # Initialise map. 
    fovmap = Map2D( visibilityMap.width, visibilityMap.height, 0)
    
    # The algorithm supports visibility reduction from one tile to the next, based on losRadius (so at losRadius we've lost all visibility)
    # We can adjust this decay using DECAY_PER_TILE_PERCENT
    decayPerTile = DECAY_PER_TILE_PERCENT/float(losRadius)
    def calc_decay( q ):
        # Helper to calculate decay percentage, based on distance to viewer
        return (q - viewerPos).length() * decayPerTile; # decay until last tile. proportional to distance

        
    def calc_adj_contrib(  col, row ):
        # calculate the number of times it has been swept
        # otgt - ivec2(2,1) + ivec2(1,1)
        x = col-1
        y = row
        total = x+y
        horz = x / float(total)
        diag = y / float(total)
        return (diag,horz)
  
    # initialise: the viewer position is always visible
    fovmap.set(viewerPos, 1)
    if onFovSetCallback:
        onFovSetCallback(viewerPos, 1)
        
    losRadiusSquared = losRadius*losRadius
        
    # do the diagonals/straight lines
    for y in range(-1,2):
        for x in range(-1,2):
            if x != 0 or y != 0:
                for i in range(1,math.ceil(losRadius)+1):
                    o = ivec2(x*i,y*i)
                    p = viewerPos + o
                    if (not fovmap.in_bounds(p)) or (o.squaredLength() > losRadiusSquared):
                        continue
                    pnb = p - ivec2(x,y)
                    amt = visibilityMap.get(pnb) * fovmap.get(pnb)
                    fovmap.set(p,amt) # don't add decay -- we're going to add that later
    
    # do the inner parts. 
    axis_sets = [
        (ivec2(1,0),ivec2(0,1)),
        (ivec2(1,0),ivec2(0,-1)),
        (ivec2(0,1),ivec2(1,0)),
        (ivec2(0,1),ivec2(-1,0)),
        (ivec2(-1,0),ivec2(0,1)),
        (ivec2(-1,0),ivec2(0,-1)),
        (ivec2(0,-1),ivec2(-1,0)),
        (ivec2(0,-1),ivec2(1,0)),
    ]
    for (fwd,up) in axis_sets:
        #fwd = ivec2(1,0)
        #up = ivec2(0,-1)
        upfwd = up+fwd
        for row in range(0,math.ceil(losRadius)+1):
            for col in range(row,math.ceil(losRadius)+1):
                if col == 0 and row == 0: # skip the first point
                    continue
                    
                o = fwd.muls(col) + up.muls(row)
                p = viewerPos + o
                if (not fovmap.in_bounds(p)) or (o.squaredLength() > losRadiusSquared):
                    continue

                amt = fovmap.get( p )
                
                pnb = p + upfwd
                vis = visibilityMap.get(p)
                if col != row and fovmap.in_bounds(pnb) and (pnb-viewerPos).squaredLength() <= losRadiusSquared:
                    contrib = calc_adj_contrib(col+1,row+1)[0] * vis
                    fovmap.add(pnb, contrib*amt)
                    
                # if the diagonal exists, the right one also exists
                pnb = p + fwd
                if row > 0 and fovmap.in_bounds(pnb) and (pnb-viewerPos).squaredLength() <= losRadiusSquared:
                    contrib = calc_adj_contrib(col+1,row)[1]* vis
                    fovmap.add(pnb, contrib*amt)
                        
                # NOW apply the decay, after we've propagated, but only if it's not straight/diag
                if row != col and col != 0 and row != 0:
                    amt = max(amt-calc_decay(p),0)
                    fovmap.set( p, amt) 
                    if onFovSetCallback:
                        onFovSetCallback(p, amt)
   
    # ADD DECAY to the diagonals/straight lines
    for y in range(-1,2):
        for x in range(-1,2):
            if x != 0 or y != 0:
                for i in range(1,math.ceil(losRadius)+1):
                    o = ivec2(x*i,y*i)
                    p = viewerPos + o
                    if (not fovmap.in_bounds(p)) or (o.squaredLength() > losRadiusSquared):
                        continue
                    amt = max(fovmap.get(p)-calc_decay(p),0)
                    fovmap.set(p,amt)
                    if onFovSetCallback:
                        onFovSetCallback(p, amt)
    
    return fovmap
    
def fov_symmetry(losRadius, visibilityMap):
    import random
    w = visibilityMap.width
    h = visibilityMap.height
    all_pts = [ivec2(o%w,o//w) for o in range(w*h)]
    num = 1000 # number of pairs to test
    pts = random.sample(all_pts,num) # pick X random points
    offsets = sortedPoints.range(1,losRadius)
    for i in range(num):
        p0 = pts[i] # pick a point
        o = random.sample(offsets,1)[0] # pick a random offset away from the point
        p1 = p0+o
        while not visibilityMap.in_bounds(p1):
            o = random.sample(offsets,1)[0]
            p1 = p0+o
        fovmap0 = fov(p0, losRadius, visibilityMap)
        fovmap1 = fov(p1, losRadius, visibilityMap)
        v0 = fovmap0.get(p1)
        v1 = fovmap1.get(p0)
        if v0 != v1:
            print("ERR",v0,v1,p0,p1)