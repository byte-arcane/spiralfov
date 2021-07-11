from mathutil import *

def load_from_file( filename ):
    # Expect a text file containing a map, w/ legend: '#' wall, '.' floor, 'X' viewer path (optional)
    lines = open(filename, 'rt').read().split('\n')
    path = []
    visibilityMap = None
    if lines:
        w = len(lines[0])
        h = len(lines)
        visibilityMap = Map2D(w,h)
        for y in range(h):
            for x in range(w):
                char = lines[y][x]
                p = ivec2(x,y)
                if char == '#':
                    visibilityMap.set(p,0)
                elif char == '.':
                    visibilityMap.set(p,1)
                elif char == '@':
                    visibilityMap.set(p,1)
                    path.append(p)
                    
    return (visibilityMap, path)
                
if __name__ == '__main__':    
    vmap, path = load_from_file("fov_demomap_1.txt")
    print(vmap)
    print(path)