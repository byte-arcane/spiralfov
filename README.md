# spiralfov
Field-of-vision algorithm that I'm using for [Age of Transcendence](https://byte-arcane.github.io/age-of-transcendence/), it's very fast and quite configurable. 

## Requirements:

Python 3, no libraries needed

## Instructions:

Run main.py to see the demo.

First you need to select one of several premade maps/scenarios (loaded from .txt files, so you can add your own)

Blockers represented with magenta, floor with green, viewer with red.
The mouse cursor corresponds to the viewer position, so you can move the viewer very quickly as you wish.
The brightness of the green colour corresponds with how visible it is (resulting visibility is a percentage)
There are several controls, using the function keys. The current configuration state is in the window title:

* F2: Blocker tiles get more transparent
* F3: Blocker tiles get less transparent
* F4: Toggle visibility mode between binary (you either see or don't see a tile) and percentage-based
* F5: When in binary visibility mode, increase the percentage threshold
* F6: When in binary visibility mode, decrease the percentage threshold
* F7: Increase the viewer line of sight radius (up to a maximum, in fov.py)
* F8: Decrease the viewer line of sight radius (down to 1)
* F9: Increase the fov algorithm's decay parameter (see fov.py for details)
* F10: Decrease the fov algorithm's decay parameter (see fov.py for details)
* F11: Export GIF and mp4 (you need extra packages for this: PIL, imageio and ffmpeg needs to be in PATH)


Note: Googling the name "Spiral FoV", it might have some similarities with [this](http://www.roguebasin.com/index.php?title=Spiral_Path_FOV), but more as a concept, as I might have heard that method in passing and that's about it.
