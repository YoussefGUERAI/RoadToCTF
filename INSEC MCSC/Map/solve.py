#!/usr/bin/env python3
"""Treasure map challenge solver: explore -> reset -> Dijkstra -> execute."""
import socket, time, re, select, sys, heapq, pickle, os, traceback

IPS = ['100.48.131.205', '54.86.2.107', '98.88.42.187']
HOST = 'challs.insec.club'
PORT = 27005

PLAIN = '·'
SWAMP = '≈'
ROCK = '▲'
PLAYER = '@'
TREASURE = 'X'
TILE_CODE = {PLAIN: 'P', SWAMP: 'S', ROCK: 'R'}

GRID_W = 1000
GRID_H = 1000
VIEW_W = 35
VIEW_H = 20
VIEW_CX = 17
VIEW_CY = 10

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
    try:
        s = socket.socket()
        s.settimeout(20)
        s.connect((HOST, PORT))
        s.setblocking(False)
        return s, HOST
    except Exception as e:
        raise RuntimeError(f'No connect: {last_exc}; {e}')

def strip_ansi(b):
    if isinstance(b, bytes):
        b = b.decode('utf-8', errors='replace')
    return re.sub(r'\x1b\[[0-9;]*m', '', b)

class Session:
    def __init__(self):
        self.sock = None
        self.buf = b''
        self.pos = None
        self.cost = 0
        self.attempts = 3
        self.start_pos = None
        self.world = {}
        self.treasure = None
        self.treasure_tile_type = None

    def connect(self):
        self.sock, ip = connect()
        print(f'[+] Connected {ip}', flush=True)

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

    def wait_prompts(self, n, max_wait=120):
        start = time.time()
        while time.time() - start < max_wait:
            text = strip_ansi(self.buf)
            matches = list(re.finditer(r'attempts=(\d+) > *', text))
            if len(matches) >= n:
                break
            ok = self.recv_some(timeout=2.0)
            if ok is None:
                raise IOError('Connection closed')
        text = strip_ansi(self.buf)
        self.buf = b''
        return text

    def send(self, cmd):
        self.sock.sendall((cmd + '\n').encode())

    def parse_header_blocks(self, text):
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
        left = cx - VIEW_CX
        top = cy - VIEW_CY
        terrain_code = {'Plain':'P','Swamp':'S','Rock':'R'}[terrain]
        for r in range(VIEW_H):
            for c in range(VIEW_W):
                x = left + c
                y = top + r
                if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
                    continue
                sym = rows[r][c]
                if sym == PLAYER:
                    self.world[(x, y)] = terrain_code
                elif sym == TREASURE:
                    self.treasure = (x, y)
                    if self.treasure_tile_type:
                        self.world[(x, y)] = {'Plain':'P','Swamp':'S','Rock':'R'}[self.treasure_tile_type]
                    else:
                        self.world[(x, y)] = '?'
                elif sym in TILE_CODE:
                    self.world[(x, y)] = TILE_CODE[sym]

    def init(self):
        self.connect()
        text = self.wait_prompts(1, max_wait=120)
        m = re.search(r'treasure is hidden on a (\w+) tile', text)
        if m:
            self.treasure_tile_type = m.group(1)
            print(f'[+] Treasure on {self.treasure_tile_type} tile', flush=True)
        prompts = self.parse_prompts(text)
        if not prompts:
            raise RuntimeError('no prompt in banner')
        self.pos = (prompts[-1][0], prompts[-1][1])
        self.cost = prompts[-1][2]
        self.attempts = prompts[-1][3]
        self.start_pos = self.pos
        print(f'[+] Start at {self.pos}, cost={self.cost}, attempts={self.attempts}', flush=True)
        self.send('color')
        self.wait_prompts(1, 10)
        self.send('view')
        t = self.wait_prompts(1, 10)
        for b in self.parse_header_blocks(t):
            self.update_map_from_view(b)
        print(f'[+] Initial map cells: {len(self.world)}', flush=True)

    def do_batch(self, cmds, max_wait=120):
        if not cmds: return ''
        for c in cmds:
            self.send(c)
        text = self.wait_prompts(len(cmds), max_wait)
        for b in self.parse_header_blocks(text):
            self.update_map_from_view(b)
        prompts = self.parse_prompts(text)
        if prompts:
            lp = prompts[-1]
            self.pos = (lp[0], lp[1])
            self.cost = lp[2]
            self.attempts = lp[3]
        return text

    def explore(self, save_path='/tmp/world_map.pkl'):
        """Snake explore: viewport is 35x20, so stride = 35 in X, 20 in Y."""
        xs = list(range(17, 983, 35))
        if xs[-1] != 982:
            xs.append(982)
        ys = list(range(10, 991, 20))
        if ys[-1] != 990:
            ys.append(990)
        waypoints = []
        for i, y in enumerate(ys):
            xlist = xs if i % 2 == 0 else list(reversed(xs))
            for x in xlist:
                waypoints.append((x, y))
        print(f'[+] {len(waypoints)} waypoints to visit', flush=True)

        def plan_move(from_xy, to_xy):
            """Commands from from_xy to to_xy, avoiding stepping on treasure."""
            cmds = []
            x, y = from_xy
            tx, ty = to_xy
            # X first
            while x != tx:
                dx = tx - x
                direction = 'E' if dx > 0 else 'W'
                step = abs(dx)
                if self.treasure:
                    trx, try_ = self.treasure
                    if try_ == y:
                        if dx > 0 and trx > x and trx <= x + step:
                            step = trx - x - 1
                        elif dx < 0 and trx < x and trx >= x - step:
                            step = x - trx - 1
                if step <= 0:
                    # go around — step 1 in Y
                    cmds.append('S 1' if y < GRID_H - 1 else 'N 1')
                    y = y + 1 if y < GRID_H - 1 else y - 1
                    continue
                cmds.append(f'{direction} {step}')
                x += step if dx > 0 else -step
            # Y
            while y != ty:
                dy = ty - y
                direction = 'S' if dy > 0 else 'N'
                step = abs(dy)
                if self.treasure:
                    trx, try_ = self.treasure
                    if trx == x:
                        if dy > 0 and try_ > y and try_ <= y + step:
                            step = try_ - y - 1
                        elif dy < 0 and try_ < y and try_ >= y - step:
                            step = y - try_ - 1
                if step <= 0:
                    cmds.append('E 1' if x < GRID_W - 1 else 'W 1')
                    x = x + 1 if x < GRID_W - 1 else x - 1
                    continue
                cmds.append(f'{direction} {step}')
                y += step if dy > 0 else -step
            return cmds, (x, y)

        t_start = time.time()
        BATCH = 30
        cmd_buffer = []
        virtual_pos = self.pos  # tracked during batching
        for i, wp in enumerate(waypoints):
            cmds, virtual_pos = plan_move(virtual_pos, wp)
            cmd_buffer.extend(cmds)
            if len(cmd_buffer) >= BATCH or i == len(waypoints) - 1:
                self.do_batch(cmd_buffer, max_wait=180)
                cmd_buffer = []
                if self.pos != virtual_pos:
                    # mismatch — likely hit an edge or something; resync
                    print(f'[!] virtual_pos {virtual_pos} != actual {self.pos}', flush=True)
                    virtual_pos = self.pos
                if i % 50 == 0 or i == len(waypoints) - 1:
                    elapsed = time.time() - t_start
                    print(f'[{elapsed:.1f}s] wp {i+1}/{len(waypoints)} pos={self.pos} map={len(self.world)} treasure={self.treasure} attempts={self.attempts}', flush=True)
                    self.save(save_path)
                if self.attempts < 3:
                    print(f'[!] ATTEMPTS DROPPED to {self.attempts}!', flush=True)
                    self.save(save_path)
                    return
        self.save(save_path)
        print(f'[+] Exploration done. cells={len(self.world)}/{GRID_W*GRID_H} treasure={self.treasure}', flush=True)

    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({
                'world': self.world, 'pos': self.pos, 'start': self.start_pos,
                'treasure': self.treasure, 'treasure_tile': self.treasure_tile_type,
                'cost': self.cost, 'attempts': self.attempts,
            }, f)

if __name__ == '__main__':
    sess = Session()
    try:
        sess.init()
        sess.explore()
    except KeyboardInterrupt:
        sess.save('/tmp/world_map.pkl')
    except Exception as e:
        traceback.print_exc()
        try: sess.save('/tmp/world_map.pkl')
        except: pass
    # Keep socket open — save pid info
    with open('/tmp/session_pid.txt', 'w') as f:
        f.write(f'sock fd: {sess.sock.fileno() if sess.sock else "none"}\n')
    # Don't close immediately — give a chance to run follow-up
    time.sleep(5)
