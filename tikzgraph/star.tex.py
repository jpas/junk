from tikzgraph import *

with picture():
    for n in range(5):
        draw_graph(star_graph(n), x=3*n)
