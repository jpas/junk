import random
import sys

from collections import *
from contextlib import *
from functools import *
from itertools import *

import networkx as nx

def nth(iterable, n, default=None):
    return next(islice(iterable, n, None), default)


# move print to stderr so we can write figures to stdout and redirect them
_print = print
def print(*args, **kwargs):
    _print(*args, file=sys.stderr, **kwargs)

def new_command(name, content):
    opt = f'[{nargs}]' if content.count('#') > 0 else ''
    _print(f'\\newcommand{{\\{name}}}{{{content}}}')

@contextmanager
def picture():
    _print(r'\begin{tikzpicture}')
    yield
    _print(r'\end{tikzpicture}')

def set_graph_data(G, pos):
    G.graph['coords'] = {}
    for e, d in G.edges.items():
        d['style'] = 'thin'
        d['kind'] = 'edge'

    for v, d in G.nodes.items():
        d['pos'] = pos.get(v)
        d['label'] = ''
        d['style'] = 'vx'

def new_graph(vs, es, pos=None):
    G = nx.Graph()
    G.add_nodes_from(vs)
    G.add_edges_from(es)
    set_graph_data(G, pos)
    return G

def draw_graph(G, x=0, y=0):
    lines = chain(
        [r'\coordinate (oo) at ({x},{y});'.format(x=x, y=y)],
        [r'\coordinate (c{i}) at ($ (oo) + {pos} $);'.format(i=i, pos=pos)
         for i, pos in G.graph['coords'].items()],
        [r'\node[{style}] (v{v}) at ($ (oo) + {pos} $) {{{label}}};'.format(v=v, **d)
         for v, d in G.nodes.items()],
        [r'\draw[{style}] (v{u}) {kind} (v{v});'.format(u=u, v=v, **d)
         for (u, v), d in G.edges.items()],
    )
    _print('\n'.join(lines))

def star_graph(n, r=1):
    vs = range(n+1)
    es = {(n, v) for v in range(n)}
    pos = {v: f'(90+360/{n}*{v}:{r})' for v in range(n)}
    pos[n] = '(0,0)'
    return new_graph(vs, es, pos)
