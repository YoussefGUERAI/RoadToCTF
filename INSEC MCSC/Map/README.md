# INSEC Treasure Map Challenge — Walkthrough

**Challenge:** `nc challs.insec.club 27005`
**Category:** Misc
**Flag:** `INSEC{oPt1m4l_p4TH_w1Th_S0mEth1ng_In_th3_W4y}`

## The problem

On connection the server prints a banner and a prompt:

```
[138,56] cost=0 attempts=3 >
```

Game rules (from the server's `rules` command):

- You are `@` on a 1000×1000 grid of `·` Plain, `≈` Swamp, `▲` Rock tiles.
- The `view` command (or any move) prints a 35×20 viewport centered on you (player at column 17, row 10).
- Commands: `N/S/E/W <steps>`, `view`, `reset`, `color`, `rules`.
- Each move has a cost based on **the tile you're leaving** and **the tile you're entering** (a 3×3 base-cost table).
- Six special `(prev, curr, next)` triples override the base cost (see `rules`).
- You have 3 attempts. `reset` costs one. Reaching the treasure with a **non-optimal** path costs one. Reaching it **optimally** reveals the flag.

Starting position, treasure location, and terrain are randomized per connection, but fixed for the lifetime of that TCP session.

## Strategy

1. **Explore** the grid by snake-walking through viewports (stride 35 in X, 20 in Y — exactly one viewport apart, no overlap). Every move renders a viewport, so we learn one 35×20 region per waypoint.
2. **Find the treasure X** during the snake walk. **Do not step on it** (that would end the game). `plan_move()` detects when a path would cross the treasure's row/column and detours around it.
3. **`reset`** to return to the start tile (costs 1 attempt → 2 remaining). The map persists.
4. **Dijkstra** on `(x, y, prev_tile)` state. The prev_tile axis is needed because the special transition costs depend on the previous tile, not just the current one. Grid is 1000×1000 × 3 states = 3M nodes — tractable in ~20s of Python.
5. **Execute** the path with all macro commands pipelined into a single `send()`. Then drain the socket until the server prints the flag.

## Key implementation notes

- **Initial handshake is slow.** The server prints `Generating map...` and stalls for ~30–90s before the banner. Use a patient read loop with a ~2 min timeout.
- **ANSI codes everywhere.** Strip with `re.sub(r'\x1b\[[0-9;]*m', '', text)` before parsing.
- **Parse the viewport** by finding the `│ [x,y]  standing on: T` header and reading the next 20 lines that start and end with `│`. Cells are single chars separated by single spaces (35 cells per row).
- **Prompt detection** uses the regex `attempts=\d+ > *` — one prompt per command response.
- **First attempt failed** because batches of 40 commands with a `wait_prompts()` per batch racked up round-trip latency and hit some server-side session limit ~560 commands into execution. The **v2 fix** is to send every execute-phase command in one `sendall()` and just drain the response — takes <5 seconds end-to-end.
- **Don't rely on the `insec{` regex match.** The flag is literal uppercase `INSEC{...}` — check both cases (or case-insensitively).

## Timing (single run)

| Phase | Time |
|-------|------|
| Connect + wait for banner | ~30s |
| Explore (1450 viewports) | ~21s |
| Reset | instant |
| Dijkstra (Python) | ~17–19s |
| Pipelined execute (730 macros) | ~5s |
| **Total** | **~75s** |

## Cost tables (copied from the server's `rules`)

Base cost `(from, to) → cost`:

| From \ To | Plain | Swamp | Rock |
|-----------|------:|------:|-----:|
| **Plain** | 1 | 4 | 7 |
| **Swamp** | 6 | 2 | 3 |
| **Rock**  | 2 | 8 | 1 |

Special `(prev, curr, next) → cost` (overrides base cost on `curr → next`):

| Prev | Curr | Next | Cost |
|------|------|------|-----:|
| Plain | Swamp | Rock | 10 |
| Rock | Plain | Swamp | 9 |
| Swamp | Rock | Plain | 11 |
| Plain | Rock | Swamp | 12 |
| Rock | Swamp | Plain | 13 |
| Swamp | Plain | Rock | 8 |

## Files in this directory

- **`solve_v2.py`** — the working solver (explore → reset → Dijkstra → pipelined execute). Run this to reproduce.
- **`solve_full.py`** — first full pipeline, died mid-execute from batched-wait round-trips. Kept for reference.
- **`solve.py`** — exploration-only scaffold; superseded.
- **`pathfind.py`** — standalone Dijkstra that reads a saved `world_map.pkl`; useful for debugging/re-runs without re-connecting.
- **`flag.txt`** — the captured flag.
- **`final_output.txt`** — the tail of the v2 run showing the server's "You found the treasure!" line.

## Reproduce

```bash
python3 solve_v2.py
```

Expect ~75 seconds. The flag appears in stdout and is also written to `/tmp/transcript.txt`.
