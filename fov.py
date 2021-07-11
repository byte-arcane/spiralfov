import math
from timeit import default_timer as timer
from enum import IntEnum
from mathutil import *

# Configuration
MAX_LOS = 20

# Smaller value (always in [0,1]) leads to less decay
DECAY_PER_TILE_PERCENT = 0.9 # e.g. Visibility reduces to 90% from a tile to the next

# calculate ONCE the list of sorted points
sortedPoints = SortedPoints(MAX_LOS)

def fov( viewerPos, losRadius, visibilityMap, onFovSetCallback = None, onFovStepCallback = None ):
    """
    Calculate the field-of-vision map (0: can't see, 1: see maximum, and anything in between)
    onFovSetCallback: callback to mark all the cells we've visited (parameters: position and visibility value)
    onFovStepCallback: callback for each iteration (parameters: position and up to two closest previous neighbours, as a list, and the amount of visibility)
    """
    
    # Initialise map. 
    fovmap = Map2D( visibilityMap.width, visibilityMap.height, 0)
    
    # The algorithm supports visibility reduction from one tile to the next, based on losRadius (so at losRadius we've lost all visibility)
    # We can adjust this decay using DECAY_PER_TILE_PERCENT
    decayPerTile = DECAY_PER_TILE_PERCENT/float(losRadius)
    def calc_decay( p ):
        # Helper to calculate decay percentage, based on distance to viewer
        return (p - viewerPos).length() * decayPerTile; # decay until last tile. proportional to distance
        
    def calc_visibility( p ):
        # visibility gets propagated multiplicatively: "visibility at tile" * "visibility propagation so far"
        return visibilityMap.get(p) * fovmap.get(p)
  
    # initialise: the viewer position is always visible
    fovmap.set(viewerPos, 1)
    if onFovSetCallback:
        onFovSetCallback(viewerPos, 1)

    maxRadiusUsed = 0 # Keep track of the max radius we've processed so far
    # For each point within losRadius, ordered by distance to origin
    for o in sortedPoints.range(1,losRadius):
        # calc absolute position
        p = o + viewerPos;
        
        # Only process points in map
        if not fovmap.in_bounds(p):
          continue
        
        # if we've made a full round in the sorted points spiral without adding a tile, early exit
        omag = o.length();
        if (omag - maxRadiusUsed) >= 2.0:
            break;

        ox_abs = abs(o.x)
        oy_abs = abs(o.y)
        amt = 0.0
        
        # calc the decay at this point
        curDecay = calc_decay(p)
        
        # diagonal or axis-aligned: previous contribution comes from a SINGLE tile
        if (ox_abs == oy_abs) or (ox_abs*oy_abs == 0):
            pnb = p-o.sign(); # get previous tile
            amt = calc_visibility(pnb)
            prevDecay = calc_decay(pnb)
            amt = max(amt + prevDecay - curDecay, 0)
            if onFovStepCallback:
                onFovStepCallback(p, [pnb], amt)
        # NOT diagonal or axis-aligned: previous contribution comes from TWO tiles, so get their contribution and mix it
        else:
            # We need to calculate the closest 2 points on the line from current point to the viewer:
            #   the closest diagonal (move back 1 unit in both X and Y)
            pnb_diag = ivec2(p.x - sign(o.x), p.y - sign(o.y));
            #   the closest non-diagonal. Move back 1 unit in the axis of greater magnitude
            if ox_abs > oy_abs: 
                pnb = ivec2(p.x - sign(o.x), p.y);
            else: #ox_abs < oy_abs
                pnb = ivec2(p.x, p.y - sign(o.y));
            
            # calculate visibility and decay for both relevant points
            amt0 = calc_visibility(pnb)
            prevDecay0 = calc_decay(pnb)
            amt1 = calc_visibility(pnb_diag)
            prevDecay1 = calc_decay(pnb_diag)
            
            # Calculate interpolation amount based on the unit vector of the offset:
            #   if we're further along X, we need more contribution from the 
            axis = 1 if ox_abs > oy_abs else 0
            n = o.abs().normalized()
            t = n[axis];
            
            prevDecay = lerp(prevDecay0, prevDecay1, t);
            amt = lerp(amt0, amt1, t);
            amt = max(amt + prevDecay - curDecay, 0.0);
            
            if onFovStepCallback:
                onFovStepCallback(p, [pnb_diag, pnb], amt)
            
        fovmap.set(p,amt)
        if onFovSetCallback:
            onFovSetCallback(p, amt)
        if amt > 0:
            maxRadiusUsed = omag
    
    return fovmap
    
def fov_symmetry(losRadius, visibilityMap):
    import random
    w = visibilityMap.width
    h = visibilityMap.height
    all_pts = [ivec2(o%w,o//w) for o in range(w*h)]
    num = 100 # number of pairs to test
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