#!/usr/bin/env python3
"""V2: ultra-fast pipelined execution."""
import socket, time, re, select, sys, heapq, pickle, os, traceback

IPS = ['100.48.131.205', '54.86.2.107', '98.88.42.187']
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
    for ip in IPS:
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
        self.transcript = b''

    def recv_some(self, timeout=3.0):
        r, _, _ = select.select([self.sock], [], [], timeout)
        if not r: return False
        try:
            chunk = self.sock.recv(65536)
            if not chunk: return None
            self.buf += chunk
            self.transcript += chunk
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
        self.buf = b''
        return text

    def send(self, cmd):
        self.sock.sendall((cmd + '\n').encode())

    def send_many(self, cmds):
        """Send all commands in a single large write."""
        data = ('\n'.join(cmds) + '\n').encode()
        # socket may need multiple sends for large data
        total = 0
        while total < len(data):
            # need blocking send or non-blocking send with wait
            self.sock.setblocking(True)
            try:
                sent = self.sock.send(data[total:])
                total += sent
            finally:
                self.sock.setblocking(False)

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
                    if 'standing on' in content: continue
                    cells = [c for c in content.strip().split(' ') if c != '']
                    if len(cells) == VIEW_W:
                        rows.append(cells)
                elif line.startswith('└'):
                    break
                if len(rows) == VIEW_H: break
            if len(rows) == VIEW_H:
                blocks.append((cx, cy, terrain, rows))
        return blocks

    def parse_prompts(self, text):
        return [(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))
                for m in re.finditer(r'\[(\d+),(\d+)\] cost=(\d+) attempts=(\d+) >', text)]

    def update_from_view(self, view):
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

    def do_batch(self, cmds, max_wait=120):
        if not cmds: return ''
        for c in cmds:
            self.send(c)
        text = self.wait_prompts(len(cmds), max_wait)
        for b in self.parse_blocks(text):
            self.update_from_view(b)
        prompts = self.parse_prompts(text)
        if prompts:
            lp = prompts[-1]
            self.pos = (lp[0], lp[1])
            self.cost = lp[2]; self.attempts = lp[3]
        return text

    def init(self):
        self.sock, ip = connect()
        print(f'[+] Connected {ip}', flush=True)
        text = self.wait_prompts(1, 120)
        m = re.search(r'treasure is hidden on a (\w+) tile', text)
        if m: self.treasure_tile = m.group(1)
        prompts = self.parse_prompts(text)
        self.pos = (prompts[-1][0], prompts[-1][1])
        self.cost = prompts[-1][2]; self.attempts = prompts[-1][3]
        self.start_pos = self.pos
        print(f'[+] Start={self.pos}, treasure_tile={self.treasure_tile}', flush=True)
        self.send('color'); self.wait_prompts(1, 10)
        self.send('view'); t = self.wait_prompts(1, 10)
        for b in self.parse_blocks(t):
            self.update_from_view(b)

    def plan_move(self, from_xy, to_xy):
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
        t_start = time.time()
        BATCH = 40
        buf = []; vp = self.pos
        for i, wp in enumerate(waypoints):
            cmds, vp = self.plan_move(vp, wp)
            buf.extend(cmds)
            if len(buf) >= BATCH or i == len(waypoints) - 1:
                self.do_batch(buf, 120)
                buf = []
                if self.pos != vp: vp = self.pos
                if i % 200 == 0 or i == len(waypoints) - 1:
                    el = time.time() - t_start
                    print(f'[{el:.1f}s] wp {i+1}/{len(waypoints)} pos={self.pos} map={len(self.world)} tre={self.treasure}', flush=True)
        print(f'[+] Explore done. tre={self.treasure}', flush=True)

    def reset(self):
        self.send('reset')
        t = self.wait_prompts(1, 30)
        prompts = self.parse_prompts(t)
        if prompts:
            lp = prompts[-1]; self.pos = (lp[0], lp[1]); self.cost = lp[2]; self.attempts = lp[3]
        print(f'[+] After reset: pos={self.pos} att={self.attempts}', flush=True)

    def dijkstra(self, start, target):
        sx, sy = start; tx, ty = target
        dist = {(sx,sy,'N'): 0}; came = {}
        pq = [(0, sx, sy, 'N')]
        while pq:
            d, x, y, p = heapq.heappop(pq)
            if dist.get((x,y,p), -1) != d: continue
            if (x, y) == (tx, ty):
                path = []; cur = (x, y, p)
                while cur in came: path.append((cur[0], cur[1])); cur = came[cur]
                path.append((sx, sy)); path.reverse()
                return d, path
            cc = self.world.get((x, y))
            if cc not in ('P','S','R'): continue
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = x+dx, y+dy
                if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H: continue
                nc = self.world.get((nx, ny))
                if nc not in ('P','S','R'): continue
                if p != 'N' and (p, cc, nc) in SPECIAL_COST: ec = SPECIAL_COST[(p, cc, nc)]
                else: ec = BASE_COST[(cc, nc)]
                nd = d + ec; ns = (nx, ny, cc)
                if dist.get(ns, 1<<30) > nd:
                    dist[ns] = nd; came[ns] = (x, y, p)
                    heapq.heappush(pq, (nd, nx, ny, cc))
        return None, None

    def path_to_cmds(self, path):
        if len(path) < 2: return []
        def dof(a, b):
            d = (b[0]-a[0], b[1]-a[1])
            return {(1,0):'E',(-1,0):'W',(0,1):'S',(0,-1):'N'}[d]
        cmds = []; i = 0
        while i < len(path) - 1:
            dr = dof(path[i], path[i+1]); cnt = 1; j = i + 1
            while j < len(path) - 1 and dof(path[j], path[j+1]) == dr:
                cnt += 1; j += 1
            cmds.append(f'{dr} {cnt}')
            i += cnt
        return cmds

    def execute_all(self, cmds):
        """Send all commands at once, then drain and look for flag."""
        print(f'[+] Pipelining all {len(cmds)} commands at once', flush=True)
        t0 = time.time()
        self.send_many(cmds)
        t1 = time.time()
        print(f'[+] All commands sent in {t1-t0:.2f}s', flush=True)
        # Drain until we see flag or connection closes
        deadline = time.time() + 300
        last_data = time.time()
        while time.time() < deadline:
            ok = self.recv_some(timeout=3.0)
            if ok is None:
                print('[+] Connection closed', flush=True)
                break
            if ok is True:
                last_data = time.time()
                # check for flag
                s = self.transcript.decode('utf-8', errors='replace')
                if 'insec{' in s:
                    print('[+] FLAG DETECTED!', flush=True)
                    break
            else:
                # timeout; if idle > 15s, assume done
                if time.time() - last_data > 15:
                    break
        return self.transcript

if __name__ == '__main__':
    s = Sess()
    try:
        s.init()
        s.explore()
        if not s.treasure:
            print('[-] No treasure!', flush=True)
            sys.exit(1)
        s.reset()
        t0 = time.time()
        cost, path = s.dijkstra(s.start_pos, s.treasure)
        print(f'[+] Dijkstra {time.time()-t0:.1f}s, cost={cost}, steps={len(path)}', flush=True)
        cmds = s.path_to_cmds(path)
        print(f'[+] {len(cmds)} macro cmds', flush=True)
        with open('/tmp/cmds.txt','w') as f: f.write('\n'.join(cmds))
        result = s.execute_all(cmds)
        with open('/tmp/transcript.bin','wb') as f: f.write(result)
        text = strip_ansi(result)
        with open('/tmp/transcript.txt','w') as f: f.write(text)
        m = re.search(r'insec\{[^}]+\}', text)
        if m:
            print(f'\n>>> FLAG: {m.group(0)} <<<\n', flush=True)
        else:
            print('[?] No flag match. Last 2000 chars:', flush=True)
            print(text[-2000:])
    except Exception as e:
        traceback.print_exc()
        try:
            with open('/tmp/transcript.bin','wb') as f: f.write(s.transcript)
        except: pass
