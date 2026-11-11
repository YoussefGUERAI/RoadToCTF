# Linux Privilege Escalation — File Capabilities (HTB Cap)

## Core idea
Linux **capabilities** split traditional root privileges into smaller permissions. A binary with a dangerous capability can sometimes be abused to escalate privileges, even without the **SUID** bit.

In HTB **Cap**, the user `nathan` could execute Python with `CAP_SETUID`, allowing the Python process to change its UID to **0 (root)**.

## Enumeration

```bash
id                         # Current UID/GID
getcap -r / 2>/dev/null     # Recursively list file capabilities; hide permission errors
```

Relevant output:

```text
/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip
```

- `CAP_SETUID`: allows privileged changes to process user IDs.
- `CAP_NET_BIND_SERVICE`: allows binding to privileged network ports (not needed here).
- `+eip`: file capability flags/sets: **e** = effective flag, **i** = inheritable, **p** = permitted. The kernel uses these, along with process capability rules, when executing the file.

## Exploitation (authorized HTB lab)

```bash
/usr/bin/python3.8 -c 'import os; os.setuid(0); os.system("/bin/bash")'
whoami
id
```

**Why it worked:**
1. Launching `/usr/bin/python3.8` gave the process the effective `CAP_SETUID` capability; it initially still ran as `nathan`.
2. `os.setuid(0)` invoked the Linux `setuid()` syscall. The kernel allowed the change because of `CAP_SETUID`.
3. `os.system("/bin/bash")` spawned a shell with UID 0; `whoami` returned `root`.

Without the capability, `os.setuid(0)` would normally fail with `Operation not permitted`. Changing UID does **not** necessarily change GID.

## SUID vs capabilities

| SUID | File capabilities |
|---|---|
| Runs a program with its owner's effective UID (often root) | Grants selected privileges without automatically changing UID |
| Find: `find / -type f -perm -4000 2>/dev/null` | Find: `getcap -r / 2>/dev/null` |

## What to remember for future challenges

- **Do not assume every capability is exploitable.** Assess the capability *and* what the binary lets you do.
- `CAP_SETUID` on an unrestricted interpreter is especially risky; `CAP_DAC_OVERRIDE` can bypass normal file permissions, while `CAP_NET_RAW` is often legitimate for tools such as `ping`.
- After getting a low-privilege shell, check `id`, `sudo -l`, SUID files, file capabilities, cron jobs, and relevant writable paths.
- A capability misconfiguration is **not a Python vulnerability**: the OS was configured to trust the interpreter with excessive privilege.

**Reference:** [GTFOBins — Python capabilities](https://gtfobins.github.io/gtfobins/python/#capabilities)
