#!/usr/bin/env python3
"""Dijkstra pathfinder for the treasure map, using state = (x, y, prev_tile)."""
import pickle, heapq, time, sys

GRID_W = 1000
GRID_H = 1000

BASE_COST = {
    ('P','P'): 1, ('P','S'): 4, ('P','R'): 7,
    ('S','P'): 6, ('S','S'): 2, ('S','R'): 3,
    ('R','P'): 2, ('R','S'): 8, ('R','R'): 1,
}
SPECIAL_COST = {
    ('P','S','R'): 10, ('R','P','S'): 9, ('S','R','P'): 11,
    ('P','R','S'): 12, ('R','S','P'): 13, ('S','P','R'): 8,
}

TILE_IDX = {'P': 0, 'S': 1, 'R': 2}
NONE_IDX = 3  # for starting state (no previous tile)

def edge_cost(prev_code, curr_code, next_code):
    """Cost to move from curr to next, given we came from prev."""
    if prev_code != 'N':
        if (prev_code, curr_code, next_code) in SPECIAL_COST:
            return SPECIAL_COST[(prev_code, curr_code, next_code)]
    return BASE_COST[(curr_code, next_code)]

def load(path='/tmp/world_map.pkl'):
    with open(path, 'rb') as f:
        return pickle.load(f)

def find_path(world, start, target):
    """Dijkstra with state (x, y, prev_tile). Returns (total_cost, path_cells)."""
    # Build tile grid
    # world is dict (x,y) -> 'P'/'S'/'R'
    # We allow unknown cells to be ignored (not visited)
    sx, sy = start
    tx, ty = target
    # State: (cost, x, y, prev_code) — prev_code is 'N' for start, else 'P'/'S'/'R'
    # prev_idx: 0,1,2,3
    prev_idx = {'P':0, 'S':1, 'R':2, 'N':3}
    idx_prev = {v:k for k,v in prev_idx.items()}
    # dist[(x,y,p)] = cost
    dist = {}
    came = {}
    start_state = (sx, sy, 'N')
    dist[start_state] = 0
    pq = [(0, sx, sy, 'N')]
    visited_count = 0
    while pq:
        d, x, y, p = heapq.heappop(pq)
        if (x, y, p) not in dist or dist[(x,y,p)] != d:
            continue
        visited_count += 1
        if (x, y) == (tx, ty):
            # Reconstruct path
            path = []
            cur = (x, y, p)
            while cur in came:
                path.append((cur[0], cur[1]))
                cur = came[cur]
            path.append((sx, sy))
            path.reverse()
            return d, path, visited_count
        curr_code = world.get((x, y))
        if curr_code not in ('P','S','R'):
            # Can we be here? Shouldn't happen but skip.
            continue
        for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            nx, ny = x+dx, y+dy
            if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H:
                continue
            next_code = world.get((nx, ny))
            if next_code not in ('P','S','R'):
                continue  # unknown cell; skip
            c = edge_cost(p, curr_code, next_code)
            nd = d + c
            nstate = (nx, ny, curr_code)
            if dist.get(nstate, float('inf')) > nd:
                dist[nstate] = nd
                came[nstate] = (x, y, p)
                heapq.heappush(pq, (nd, nx, ny, curr_code))
    return None, None, visited_count

def path_to_cmds(path):
    """Convert path (list of (x,y)) to command sequence, condensed."""
    cmds = []
    i = 1
    while i < len(path):
        x0, y0 = path[i-1]
        x1, y1 = path[i]
        dx, dy = x1-x0, y1-y0
        if dx != 0:
            direction = 'E' if dx > 0 else 'W'
        else:
            direction = 'S' if dy > 0 else 'N'
        # extend
        j = i
        while j < len(path):
            px, py = path[j-1]
            nx, ny = path[j]
            ndx, ndy = nx-px, ny-py
            if direction == 'E' and (ndx, ndy) == (1, 0): j += 1
            elif direction == 'W' and (ndx, ndy) == (-1, 0): j += 1
            elif direction == 'N' and (ndx, ndy) == (0, -1): j += 1
            elif direction == 'S' and (ndx, ndy) == (0, 1): j += 1
            else: break
        steps = j - i + 1
        cmds.append(f'{direction} {steps}')
        i = j + 1
    # fix: steps should be j-i (number of moves in this direction)
    # Let me redo more carefully.
    return cmds

def path_to_cmds_v2(path):
    """Path is list of positions. Group consecutive same-direction moves."""
    cmds = []
    if len(path) < 2:
        return cmds
    def dir_of(a, b):
        dx = b[0] - a[0]; dy = b[1] - a[1]
        if dx == 1 and dy == 0: return 'E'
        if dx == -1 and dy == 0: return 'W'
        if dx == 0 and dy == 1: return 'S'
        if dx == 0 and dy == -1: return 'N'
        return None
    i = 0
    while i < len(path) - 1:
        d = dir_of(path[i], path[i+1])
        count = 1
        j = i + 1
        while j < len(path) - 1:
            if dir_of(path[j], path[j+1]) == d:
                count += 1; j += 1
            else:
                break
        cmds.append(f'{d} {count}')
        i += count
    return cmds

if __name__ == '__main__':
    data = load('/tmp/world_map.pkl')
    world = data['world']
    start = data['start']
    treasure = data['treasure']
    print(f'Start: {start}, Treasure: {treasure}')
    print(f'Known cells: {len(world)}')
    if not treasure:
        print('No treasure found yet!')
        sys.exit(1)
    t0 = time.time()
    cost, path, visited = find_path(world, start, treasure)
    t1 = time.time()
    print(f'Dijkstra: {t1-t0:.2f}s, visited {visited} states')
    print(f'Path length: {len(path) if path else None} cells, cost {cost}')
    if path:
        cmds = path_to_cmds_v2(path)
        print(f'Commands ({len(cmds)}):')
        for c in cmds[:30]:
            print(' ', c)
        if len(cmds) > 30: print('  ...')
