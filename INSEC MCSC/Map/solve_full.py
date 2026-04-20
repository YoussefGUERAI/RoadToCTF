#!/usr/bin/env python3
"""Full pipeline: explore -> find X -> reset -> Dijkstra -> execute -> flag."""
import socket, time, re, select, sys, heapq, pickle, os, traceback

IPS = ['100.48.131.205', '54.86.2.107', '98.88.42.187']
HOST = 'challs.insec.club'
PORT = 27005

PLAIN = '·'; SWAMP = '≈'; ROCK = '▲'; PLAYER = '@'; TREASURE = 'X'
TILE_CODE = {PLAIN: 'P', SWAMP: 'S', ROCK: 'R'}
GRID_W = 1000; GRID_H = 1000
VIEW_W = 35; VIEW_H = 20; VIEW_CX = 17; VIEW_CY = 10

BASE_COST = {
    ('P','P'): 1, ('P','S'): 4, ('P','R'): 7,
    ('S','P'): 6, ('S','S'): 2, ('S','R'): 3,
    ('R','P'): 2, ('R','S'): 8, ('R','R'): 1,
}
SPECIAL_COST = {
    ('P','S','R'): 10, ('R','P','S'): 9, ('S','R','P'): 11,
    ('P','R','S'): 12, ('R','S','P'): 13, ('S','P','R'): 8,
}

def connect():
    last_exc = None
    for ip in IPS + [HOST]:
        try:
            s = socket.socket()
            s.settimeout(20)
            s.connect((ip, PORT))
            s.setblocking(False)
            return s, ip
        except Exception as e:
            last_exc = e
    raise RuntimeError(f'No connect: {last_exc}')

def strip_ansi(b):
    if isinstance(b, bytes):
        b = b.decode('utf-8', errors='replace')
    return re.sub(r'\x1b\[[0-9;]*m', '', b)

class Sess:
    def __init__(self):
        self.sock = None; self.buf = b''
        self.pos = None; self.cost = 0; self.attempts = 3
        self.start_pos = None
        self.world = {}
        self.treasure = None
        self.treasure_tile = None
        self.all_text = []  # accumulated text for post-mortem flag extraction

    def recv_some(self, timeout=3.0):
        r, _, _ = select.select([self.sock], [], [], timeout)
        if not r: return False
        try:
            chunk = self.sock.recv(65536)
            if not chunk: return None
            self.buf += chunk
            return True
        except BlockingIOError:
            return False

    def wait_prompts(self, n, max_wait=180):
        start = time.time()
        while time.time() - start < max_wait:
            text = strip_ansi(self.buf)
            if len(re.findall(r'attempts=(\d+) > *', text)) >= n:
                break
            ok = self.recv_some(timeout=2.0)
            if ok is None:
                raise IOError('Connection closed')
        text = strip_ansi(self.buf)
        self.all_text.append(text)
        self.buf = b''
        return text

    def send(self, cmd):
        self.sock.sendall((cmd + '\n').encode())

    def parse_blocks(self, text):
        blocks = []
        for m in re.finditer(r'\[(\d+),(\d+)\]\s+standing on:\s*(\w+)', text):
            cx, cy = int(m.group(1)), int(m.group(2))
            terrain = m.group(3)
            after = text[m.end():]
            rows = []
            for line in after.split('\n'):
                line = line.rstrip()
                if line.startswith('│') and line.endswith('│'):
                    content = line[1:-1]
                    if 'standing on' in content:
                        continue
                    cells = [c for c in content.strip().split(' ') if c != '']
                    if len(cells) == VIEW_W:
                        rows.append(cells)
                elif line.startswith('└'):
                    break
                if len(rows) == VIEW_H:
                    break
            if len(rows) == VIEW_H:
                blocks.append((cx, cy, terrain, rows))
        return blocks

    def parse_prompts(self, text):
        return [(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
                for m in re.finditer(r'\[(\d+),(\d+)\] cost=(\d+) attempts=(\d+) >', text)]

    def update_map_from_view(self, view):
        cx, cy, terrain, rows = view
        left = cx - VIEW_CX; top = cy - VIEW_CY
        tcode = {'Plain':'P','Swamp':'S','Rock':'R'}[terrain]
        for r in range(VIEW_H):
            for c in range(VIEW_W):
                x = left + c; y = top + r
                if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H: continue
                sym = rows[r][c]
                if sym == PLAYER:
                    self.world[(x, y)] = tcode
                elif sym == TREASURE:
                    self.treasure = (x, y)
                    if self.treasure_tile:
                        self.world[(x, y)] = {'Plain':'P','Swamp':'S','Rock':'R'}[self.treasure_tile]
                    else:
                        self.world[(x, y)] = '?'
                elif sym in TILE_CODE:
                    self.world[(x, y)] = TILE_CODE[sym]

    def do_batch(self, cmds, max_wait=180):
        if not cmds: return ''
        for c in cmds:
            self.send(c)
        text = self.wait_prompts(len(cmds), max_wait)
        for b in self.parse_blocks(text):
            self.update_map_from_view(b)
        prompts = self.parse_prompts(text)
        if prompts:
            lp = prompts[-1]
            self.pos = (lp[0], lp[1])
            self.cost = lp[2]
            self.attempts = lp[3]
        return text

    def init(self):
        self.sock, ip = connect()
        print(f'[+] Connected {ip}', flush=True)
        text = self.wait_prompts(1, 120)
        m = re.search(r'treasure is hidden on a (\w+) tile', text)
        if m:
            self.treasure_tile = m.group(1)
            print(f'[+] Treasure on {self.treasure_tile}', flush=True)
        prompts = self.parse_prompts(text)
        self.pos = (prompts[-1][0], prompts[-1][1])
        self.cost = prompts[-1][2]; self.attempts = prompts[-1][3]
        self.start_pos = self.pos
        print(f'[+] Start: {self.pos}', flush=True)
        self.send('color'); self.wait_prompts(1, 10)
        self.send('view'); t = self.wait_prompts(1, 10)
        for b in self.parse_blocks(t):
            self.update_map_from_view(b)
        print(f'[+] Initial map cells: {len(self.world)}', flush=True)

    def plan_move(self, from_xy, to_xy):
        """Simple L-shape path from from_xy -> to_xy avoiding stepping on treasure."""
        cmds = []; x, y = from_xy; tx, ty = to_xy
        while x != tx:
            dx = tx - x; step = abs(dx); direction = 'E' if dx > 0 else 'W'
            if self.treasure:
                trx, try_ = self.treasure
                if try_ == y:
                    if dx > 0 and x < trx <= x + step: step = trx - x - 1
                    elif dx < 0 and x - step <= trx < x: step = x - trx - 1
            if step <= 0:
                if y < GRID_H - 1: cmds.append('S 1'); y += 1
                else: cmds.append('N 1'); y -= 1
                continue
            cmds.append(f'{direction} {step}')
            x = x + step if dx > 0 else x - step
        while y != ty:
            dy = ty - y; step = abs(dy); direction = 'S' if dy > 0 else 'N'
            if self.treasure:
                trx, try_ = self.treasure
                if trx == x:
                    if dy > 0 and y < try_ <= y + step: step = try_ - y - 1
                    elif dy < 0 and y - step <= try_ < y: step = y - try_ - 1
            if step <= 0:
                if x < GRID_W - 1: cmds.append('E 1'); x += 1
                else: cmds.append('W 1'); x -= 1
                continue
            cmds.append(f'{direction} {step}')
            y = y + step if dy > 0 else y - step
        return cmds, (x, y)

    def explore(self):
        xs = list(range(17, 983, 35))
        if xs[-1] != 982: xs.append(982)
        ys = list(range(10, 991, 20))
        if ys[-1] != 990: ys.append(990)
        waypoints = []
        for i, y in enumerate(ys):
            xlist = xs if i % 2 == 0 else list(reversed(xs))
            for x in xlist:
                waypoints.append((x, y))
        print(f'[+] {len(waypoints)} waypoints', flush=True)
        t_start = time.time()
        BATCH = 30
        cmd_buf = []; vp = self.pos
        for i, wp in enumerate(waypoints):
            cmds, vp = self.plan_move(vp, wp)
            cmd_buf.extend(cmds)
            if len(cmd_buf) >= BATCH or i == len(waypoints) - 1:
                self.do_batch(cmd_buf, 180)
                cmd_buf = []
                if self.pos != vp:
                    vp = self.pos  # resync
                if i % 100 == 0 or i == len(waypoints) - 1:
                    el = time.time() - t_start
                    print(f'[{el:.1f}s] wp {i+1}/{len(waypoints)} pos={self.pos} map={len(self.world)} tre={self.treasure} att={self.attempts}', flush=True)
                    self.save('/tmp/world_map.pkl')
                if self.attempts < 3:
                    print(f'[!] attempts dropped {self.attempts}', flush=True)
                    return
        self.save('/tmp/world_map.pkl')
        print(f'[+] Explore done. cells={len(self.world)}, tre={self.treasure}', flush=True)

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({
                'world': self.world, 'pos': self.pos, 'start': self.start_pos,
                'treasure': self.treasure, 'treasure_tile': self.treasure_tile,
                'cost': self.cost, 'attempts': self.attempts,
            }, f)

    def reset(self):
        print('[+] Resetting...', flush=True)
        self.send('reset')
        t = self.wait_prompts(1, 30)
        print('[reset resp]', t[-300:], flush=True)
        prompts = self.parse_prompts(t)
        if prompts:
            lp = prompts[-1]
            self.pos = (lp[0], lp[1])
            self.cost = lp[2]; self.attempts = lp[3]
        print(f'[+] After reset: pos={self.pos}, cost={self.cost}, attempts={self.attempts}', flush=True)

    def dijkstra(self, start, target):
        sx, sy = start; tx, ty = target
        dist = {}; came = {}
        init = (sx, sy, 'N')
        dist[init] = 0
        pq = [(0, sx, sy, 'N')]
        while pq:
            d, x, y, p = heapq.heappop(pq)
            if dist.get((x,y,p), -1) != d: continue
            if (x, y) == (tx, ty):
                path = []
                cur = (x, y, p)
                while cur in came:
                    path.append((cur[0], cur[1]))
                    cur = came[cur]
                path.append((sx, sy))
                path.reverse()
                return d, path
            cc = self.world.get((x, y))
            if cc not in ('P','S','R'): continue
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H: continue
                nc = self.world.get((nx, ny))
                if nc not in ('P','S','R'): continue
                if p != 'N' and (p, cc, nc) in SPECIAL_COST:
                    ec = SPECIAL_COST[(p, cc, nc)]
                else:
                    ec = BASE_COST[(cc, nc)]
                nd = d + ec
                ns = (nx, ny, cc)
                if dist.get(ns, 1<<30) > nd:
                    dist[ns] = nd
                    came[ns] = (x, y, p)
                    heapq.heappush(pq, (nd, nx, ny, cc))
        return None, None

    def path_to_cmds(self, path):
        if len(path) < 2: return []
        def dof(a, b):
            d = (b[0]-a[0], b[1]-a[1])
            return {(1,0):'E',(-1,0):'W',(0,1):'S',(0,-1):'N'}[d]
        cmds = []
        i = 0
        while i < len(path) - 1:
            dr = dof(path[i], path[i+1])
            cnt = 1; j = i + 1
            while j < len(path) - 1 and dof(path[j], path[j+1]) == dr:
                cnt += 1; j += 1
            cmds.append(f'{dr} {cnt}')
            i += cnt
        return cmds

    def execute_path(self, cmds):
        print(f'[+] Executing {len(cmds)} commands, total moves={sum(int(c.split()[1]) for c in cmds)}', flush=True)
        BATCH = 40
        for i in range(0, len(cmds), BATCH):
            batch = cmds[i:i+BATCH]
            t = self.do_batch(batch, 120)
            # check if we found treasure
            if 'treasure' in t.lower() or 'flag' in t.lower() or 'insec{' in t.lower() or 'congratulations' in t.lower():
                print('=== TREASURE HIT — FULL RESPONSE ===')
                print(t[-3000:])
                return t
            print(f'  [exec] {i+len(batch)}/{len(cmds)} pos={self.pos} cost={self.cost} att={self.attempts}', flush=True)
        # Final drain — read anything remaining
        time.sleep(2)
        for _ in range(5):
            self.recv_some(2.0)
        final = strip_ansi(self.buf)
        print('=== FINAL BUFFER ===')
        print(final[-3000:])
        return final

if __name__ == '__main__':
    s = Sess()
    try:
        s.init()
        s.explore()
        if not s.treasure:
            print('[-] No treasure found! Saving and exiting.', flush=True)
            s.save('/tmp/world_map.pkl')
            sys.exit(1)
        print(f'[+] Treasure at {s.treasure}. Resetting...', flush=True)
        s.reset()
        if s.pos != s.start_pos:
            print(f'[!] Reset position {s.pos} != start {s.start_pos}', flush=True)
        print('[+] Running Dijkstra...', flush=True)
        t0 = time.time()
        cost, path = s.dijkstra(s.start_pos, s.treasure)
        t1 = time.time()
        print(f'[+] Dijkstra: {t1-t0:.2f}s, cost={cost}, steps={len(path) if path else 0}', flush=True)
        if not path:
            print('[-] No path found!', flush=True)
            sys.exit(1)
        cmds = s.path_to_cmds(path)
        print(f'[+] {len(cmds)} macro commands', flush=True)
        with open('/tmp/path_cmds.txt', 'w') as f:
            f.write('\n'.join(cmds))
        result = s.execute_path(cmds)
        # Save full transcript
        with open('/tmp/final_transcript.txt', 'w') as f:
            f.write(''.join(s.all_text))
            f.write('\n=== FINAL ===\n')
            f.write(result)
        # Search for flag
        flag_m = re.search(r'insec\{[^}]+\}', ''.join(s.all_text) + result)
        if flag_m:
            print(f'\n!!! FLAG: {flag_m.group(0)} !!!', flush=True)
        else:
            print('[?] No flag pattern found — check /tmp/final_transcript.txt', flush=True)
    except Exception as e:
        traceback.print_exc()
        try:
            s.save('/tmp/world_map.pkl')
            with open('/tmp/final_transcript.txt', 'w') as f:
                f.write(''.join(s.all_text))
        except: pass
