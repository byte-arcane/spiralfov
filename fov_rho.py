import math
from timeit import default_timer as timer
from enum import IntEnum
from mathutil import *


MAX_LOS = 50 # arbitrary -- there's no precalculation based on this
# Smaller value (always in [0,1]) leads to less decay
DECAY_PER_TILE_PERCENT = 0.0 # e.g. Visibility reduces to 90% from a tile to the next

"""
    FoV algorithm based on the implicit rhombus mesh of each octant
    
    Logic bug:
        for each cell, I want to combine both sources of visibility. Combine == ADD
        ... but I propagate forward only ONE of the two
        SOL1: use MAX instead of ADD
            but then another bug: I use contribution so that I can add: amt1*contrib1 + amt2*contrib2
            If I do max, I only ever get one of the two contributions
        SOL2: use MAX instead of ADD but ALSO: instead of adding using contribution, replace if contribution exceeds
        
    2 versions in cache?
"""

# cache for storing BOTH incoming visibility values for a point
# when we PROPAGATE visibility, we choose ONE of our sources. Therefore, we avoid any large parallelogram visibility integrals
# we dynamically resize it, so empty is fine here
cache = []
def fov( viewerPos, losRadius, visibilityMap, onFovSetCallback = None, debugPos = None, fnContributorsToDebugPos = None):
    """
    Calculate the field-of-vision map (0: can't see, 1: see maximum, and anything in between)
    onFovSetCallback: callback to mark all the cells we've visited (parameters: position and visibility value)
    """
    global cache
    
    # Initialise map. 
    fovmap = Map2D( visibilityMap.width, visibilityMap.height, 0)
    
    # The algorithm supports visibility reduction from one tile to the next, based on losRadius (so at losRadius we've lost all visibility)
    # We can adjust this decay using DECAY_PER_TILE_PERCENT
    decayPerTile = DECAY_PER_TILE_PERCENT/float(losRadius)
    decayPerTile = 0
    
    def calc_decay( q ):
        # Helper to calculate decay percentage, based on distance of a point q to the viewer
        return (q - viewerPos).length() * decayPerTile; # decay until last tile. proportional to distance
  
    # initialise: the viewer position is always visible
    fovmap.set(viewerPos, 1)
    if onFovSetCallback:
        onFovSetCallback(viewerPos, 1)
        
    losRadiusSquared = losRadius*losRadius
    rmax = math.ceil(losRadius)+1
        
    # do the diagonals/straight lines
    for y in range(-1,2):
        for x in range(-1,2):
            if x != 0 or y != 0:
                for i in range(1,rmax):
                    o = ivec2(x*i,y*i)
                    p = viewerPos + o
                    # handle out-of-bounds and further from los radius
                    if (not fovmap.in_bounds(p)) or (o.squaredLength() > losRadiusSquared):
                        continue
                    pnb = p - ivec2(x,y)
                    # propagate visibility multiplicatively based on last cell's values
                    amt = visibilityMap.get(pnb) * fovmap.get(pnb)
                    fovmap.set(p,amt) # don't add decay -- we're going to add that later
      
    # resize the cache to fit everything. 
    # Each cache element contains 3 entries: diagonal input, straight input, source cells contributing to this
    cache_len = rmax*rmax
    if len(cache) < cache_len:
        remain = cache_len - len(cache)
        cache += [[0,0,[]] for i in range(remain)]
    
    
    # do the inner octant parts. Represent them as a "forward" direction (along the straight line) and an "up" direction, perpendicular to the forward, towards the diagonal
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
    
    def calc_idx( for_diag, col_new, row_new):
        col_new -= row_new # convert to square
        n = ivec2(col_new, row_new).normalized()
        if for_diag: # we are lower.
            n0 = ivec2(col_new-2, row_new-2).normalized()
            n1 = ivec2(col_new-2, row_new-1).normalized()
            return 0 if dot(n0,n) > dot(n1,n) else 1
        else:
            n0 = ivec2(col_new-2, row_new-1).normalized()
            n1 = ivec2(col_new-2, row_new-0).normalized()
            return 0 if dot(n0,n) > dot(n1,n) else 1
    
    for (fwd,up) in axis_sets:
        diag = up+fwd
        for c in cache:
            c[0] = c[1] = 0
            c[2] = []
        for row in range(0,rmax):
            for col in range(row,rmax):
                # skip the first point, already calculated and contributes to no inner point directly
                if col == 0 and row == 0: 
                    continue
                    
                is_inner_octant_pt = row != col and col != 0 and row != 0
                    
                # calculate the offset
                o = fwd.muls(col) + up.muls(row)
                
                # calculate the absolute position
                p = viewerPos + o
                # if not in bounds, or further than max los, skip
                if (not fovmap.in_bounds(p)) or (o.squaredLength() > losRadiusSquared):
                    continue
                    
                do_debug = debugPos and debugPos == p
                
                # get current visibility FOR the cell, and the visibility AT the cell
                amt_cache = cache[col+row*rmax] if is_inner_octant_pt else fovmap.get(p)
                #amt = max(amt_cache[0],amt_cache[1]) if is_inner_octant_pt else amt_cache
                amt = amt_cache[0] + amt_cache[1] if is_inner_octant_pt else amt_cache
                vis = visibilityMap.get(p)
                
                # we'll be using that to multiply the pnbs
                mult = col / (col+1.0)
                
                # cache element order is processing order: diagonal == 0, straight==1
                
                # see if we need to update our top-right neighbour
                pnb = p + diag
                if col != row and fovmap.in_bounds(pnb) and (pnb-viewerPos).squaredLength() <= losRadiusSquared:
                    # calculate this tile's contribution 
                    pnbf = (row+1)*mult
                    contribution = 1- (pnbf - row) # we're coming from lower, so if pnbf at the floor, we want max contribution
                    c = cache[(col+1)+(row+1)*rmax]
                    idx = calc_idx(True, col+1, row+1)
                    amt_cur = amt_cache[idx] if is_inner_octant_pt else amt_cache 
                    amt_cur *= contribution*vis
                    #c[0] = max(c[0], amt_cur) # write to the DIAG element
                    c[0] += amt_cur
                    
                    if do_debug and amt_cur > 0:
                        c[2].append( (p- ivec2(1,0) if idx == 1 else p- ivec2(1,1),amt_cur))
                        
                # see if we need to update our right neighbour
                pnb = p + fwd
                if row > 0 and fovmap.in_bounds(pnb) and (pnb-viewerPos).squaredLength() <= losRadiusSquared:
                    pnby = row*mult
                    contribution = 1- (row-pnby) # we're coming from upper, so if pnby at the top, we want max contribution
                    c = cache[(col+1)+row*rmax]
                    idx = calc_idx(False, col+1, row)
                    amt_cur = amt_cache[idx] if is_inner_octant_pt else amt_cache 
                    amt_cur *= contribution*vis
                    #c[1] = max(c[1], amt_cur) # write to the HORZ element
                    c[1] += amt_cur
                    
                    if do_debug and amt_cur > 0:
                        c[2].append( (p- ivec2(1,0) if idx == 1 else p- ivec2(1,1),amt_cur))
                        
                # NOW apply the decay, after we've propagated, but only if it's not straight/diag
                # Because we're never going to use these values again, while the straight/diagonals could be used in other octants
                if is_inner_octant_pt:
                    amt = max(amt-calc_decay(p),0)
                    fovmap.set( p, amt) 
                    if onFovSetCallback:
                        onFovSetCallback(p, amt)
                        
                if do_debug:
                    fnContributorsToDebugPos(c[2])
   
    # ADD DECAY to the diagonals/straight lines
    for y in range(-1,2):
        for x in range(-1,2):
            if x != 0 or y != 0:
                for i in range(1,rmax):
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