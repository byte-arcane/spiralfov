import os
import tkinter as tk

import fov_demoutil
import fov
from mathutil import *

# Get all maps
mapnames = os.listdir('maps')
visibilityMaps = [ fov_demoutil.load_from_file(f'maps/{x}')[0] for x in mapnames]
QUERY = "Select a map:\n" + "\n".join([ f"{i+1}. {x}"for i,x in enumerate(mapnames)])
USE_VISIBILITY_MAP = 0
print(QUERY)
selection = input()
while True:
    done = False
    try:
        USE_VISIBILITY_MAP = int(selection)-1
        done = USE_VISIBILITY_MAP >= 0 and USE_VISIBILITY_MAP < len(visibilityMaps)
    except:
        pass
    if not done:
        print("ERROR. " + QUERY)
        selection = input()
    else:
        break
visibilityMap = visibilityMaps[USE_VISIBILITY_MAP]

TILE_SIZE = 8
LOS = 9

g_canvas_rects = None
g_prev_elems = {}
g_binary_visibility = False
g_binary_visibility_threshold = 3
def rebuild_canvas(canvas, src, los, visibilityMap):
    global g_canvas_rects
    global g_prev_elems
    
    w = visibilityMap.width
    h = visibilityMap.height
    updated_elems = {}
    def cb(p,v):
        updated_elems[p] = v
    fovmap = fov.fov( src, los, visibilityMap, cb)
    process_elems = updated_elems.copy()
    fcolor = ""
    first_time = g_canvas_rects is None
    if first_time:
        g_canvas_rects = [None] * len(visibilityMap.data)
        # First time we have to process ALL elements. So set all invisible elements to 0
        for y in range(h):
            for x in range(w):
                p = ivec2(x,y)
                if p not in updated_elems.keys():
                    process_elems[p] = 0
    else:
        #print(len(g_prev_elems))
        for k,v in g_prev_elems.items():
            if k not in updated_elems.keys(): # if previous point not in updated elements, set visibility to 0
                process_elems[k] = 0
    for p, v in process_elems.items():
        x = p.x
        y = p.y
        vq = int(v*10)
        if g_binary_visibility:
            vq = 0 if g_binary_visibility_threshold >= vq else 10
        blocker = visibilityMap.get(p) < 1
        if src == p:
            fcolor = 'red'
        elif blocker:
            fcolor = 'magenta'
        else:
            fcolor = "#0{0}0".format(hex(6+vq-1)[2:])
        if first_time:
            g_canvas_rects[x+y*w] = canvas.create_rectangle(x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE, fill= fcolor)
        else:
            canvas.itemconfig(g_canvas_rects[x+y*w], fill=fcolor)
    g_prev_elems = updated_elems

g_cursor = ivec2(0,0)
g_last_calculated_cursor = ivec2(-1,-1)

window = tk.Tk()
max_screen_width = window.winfo_screenwidth()
max_screen_height = window.winfo_screenheight()- 50 # remove a bit for title bar or taskbar
TILE_SIZE = min(max_screen_width//visibilityMap.width, max_screen_height//visibilityMap.height)


screenw = TILE_SIZE*visibilityMap.width
screenh = TILE_SIZE*visibilityMap.height
window.geometry("{0}x{1}".format(screenw,screenh))

canvas = tk.Canvas(window, bg='#000000',
           width=screenw,
           height=screenh)
canvas.pack()


rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
g_last_calculated_cursor = g_cursor
g_blocker_transparency = 0

def update_title():
    window.title(f"Cursor at {g_cursor}, LOS radius: {LOS}, blocker_transparency: {g_blocker_transparency}, binary visibility: {g_binary_visibility}, binary visibility threshold {g_binary_visibility_threshold*0.1}, fov decay percent: {fov.DECAY_PER_TILE_PERCENT}")

def canvas_coords(evt):
    global g_cursor
    global g_last_calculated_cursor
    x, y = canvas.canvasx(evt.x), canvas.canvasy(evt.y)
    t = ivec2(int(x) // TILE_SIZE, int(y) // TILE_SIZE)
    if visibilityMap.in_bounds( t ):
        g_cursor = t
        update_title()
        if not (g_last_calculated_cursor == g_cursor):
            g_last_calculated_cursor = g_cursor
            rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)

def blocker_change_transparency():    
    global visibilityMap
    visibilityMap.data = [ (x if x == 1 else g_blocker_transparency) for x in visibilityMap.data]
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)

def blocker_more_transparent(evt):
    global g_blocker_transparency
    g_blocker_transparency = min(g_blocker_transparency + 0.1,0.9999)
    blocker_change_transparency()
    
def blocker_less_transparent(evt):
    global g_blocker_transparency
    g_blocker_transparency = max(g_blocker_transparency - 0.1,0)
    blocker_change_transparency()
    
def toggle_binary_visibility(evt):
    global g_binary_visibility
    g_binary_visibility = not g_binary_visibility
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
def binary_visibility_threshold_up(evt):
    global g_binary_visibility_threshold
    g_binary_visibility_threshold = min(g_binary_visibility_threshold+1,10)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
def binary_visibility_threshold_down(evt):
    global g_binary_visibility_threshold
    g_binary_visibility_threshold = max(g_binary_visibility_threshold-1,0)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
def binary_los_up(evt):
    global LOS
    LOS = min(LOS+1, fov.MAX_LOS)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
def binary_los_down(evt):
    global LOS
    LOS = max(LOS-1,1)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
    
def fov_decay_up(evt):
    fov.DECAY_PER_TILE_PERCENT = min(fov.DECAY_PER_TILE_PERCENT+0.1, 1.0)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
    
def fov_decay_down(evt):
    fov.DECAY_PER_TILE_PERCENT = max(fov.DECAY_PER_TILE_PERCENT-0.1, 0.0)
    update_title()
    rebuild_canvas(canvas, g_cursor, LOS, visibilityMap)
            
canvas.bind('<Motion>', canvas_coords)
canvas.bind('<Enter>', canvas_coords)  # handle <Alt>+<Tab> switches between windows    
window.bind('<F2>', blocker_more_transparent)
window.bind('<F3>', blocker_less_transparent)
window.bind('<F4>', toggle_binary_visibility)
window.bind('<F5>', binary_visibility_threshold_up)
window.bind('<F6>', binary_visibility_threshold_down)
window.bind('<F7>', binary_los_up)
window.bind('<F8>', binary_los_down)
window.bind('<F9>', fov_decay_up)
window.bind('<F10>', fov_decay_down)

tk.mainloop()