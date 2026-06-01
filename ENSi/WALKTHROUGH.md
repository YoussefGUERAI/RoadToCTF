# DFIR / Memory Forensics CTF — Walkthrough

> Reconstructing the case from a 2 GB Windows VMware memory image (`memory.vmem`) and the disk artefact `MyBackup/` (an archive of the victim user's Desktop, Documents, and Downloads). Volatility 3 (v2.28.0) was the primary tool.

---

## 0. Setup

```bash
export MEM=../Desktop/memory.vmem
export OUT=../Desktop/dumps
```

---

## 1. First Look — What Are We Dealing With?

The starting picture:

- `memory.vmem` — Windows 10 memory image, ~2 GB.
- A flag format hint of `CSP{...}`.

Two processes of interest were eventually identified:

| PID  | Process       | Why it matters                                |
|------|---------------|-----------------------------------------------|
| 9152 | `notepad.exe` | Hosts the injected payload (`svchost.dll`)    |
| 9176 | (target)      | Memmap'd for full-process bytes               |
| 9180 | (target)      | Memmap'd for full-process bytes               |

---

## 2. Dumping Process Memory

```bash
python3 vol.py -f $MEM -o $OUT windows.memmap --pid 9176 --dump
python3 vol.py -f $MEM -o $OUT windows.memmap --pid 9180 --dump
```

`windows.memmap --dump` writes a contiguous reconstruction of the process's virtual address space to `pid.<PID>.dmp` inside `$OUT/`. These dumps are the raw substrate for keyword hunting.

---

## 3. Hunting the Flag String in RAM

A first pass for the flag pattern `CSP{` in both **ASCII** and **UTF-16LE** (Windows wide-char strings):

```python
python3 << 'EOF'
import re
data = open('../Desktop/memory.vmem', 'rb').read()
for enc_name, needle in [('ASCII', b'CSP{'),
                         ('UTF-16LE', b'C\x00S\x00P\x00{\x00')]:
    offsets = [m.start() for m in re.finditer(re.escape(needle), data)]
    print(f"{enc_name}: {len(offsets)} hits")
EOF
```

Result:

```
ASCII   : 86 hits
UTF-16LE: 93 hits
```

…but **every single one** of them was decoy traffic from Chrome / Edge cached pages:

```
CSP{FAKE_FLAG} Hhh wax mnytk sir ghayrha sir
CSP{FAKE_FLAG_HH} Go to anouther palce
```

i.e. the user had literally Googled the flag pattern. A red herring planted by the challenge author.

Running the same regex against the per-process dumps confirmed it:

```
=== pid.9152.dmp ===
  [UTF-16LE] CSP{FAKE_FLAG_HH}
  [ASCII]    CSP{FAKE_FLAG}
  [UTF-16LE] CSP{FAKE_FLAG}
```

**Lesson:** the flag is **not** in plaintext anywhere in RAM. Pivot from "find the flag string" to "find the malware".

---

## 4. Looking for Injected Code (`malfind`)

```bash
python3 vol.py -f $MEM -o $OUT windows.malfind --pid 9152 --dump > malfind_9152.txt
python3 vol.py -f $MEM -o $OUT windows.malfind --pid 9176 --dump > malfind_9176.txt
```

Both files came back empty (header only) — no classic `RWX` shellcode-style VAD regions. So the injection is **not** raw shellcode; it's a properly-loaded image. That points at a reflective / DLL-side-loading style.

---

## 5. VAD Inspection — Catching the Suspicious DLL

```bash
python3 vol.py -f $MEM windows.vadinfo --pid 9152 > vad_9152.txt
grep -iE "PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY" vad_9152.txt
```

Scrolling through the executable mappings of `notepad.exe`, one line stands out from a sea of legitimate System32 DLLs:

```
9152  notepad.exe  0x7fff64c50000  0x7fff64c5bfff  PAGE_EXECUTE_WRITECOPY
                   \Users\Mr_Togoo\svchost.dll
```

A DLL named `svchost.dll`, **loaded from a user profile path**, mapped into `notepad.exe`. That is wildly off-baseline:

- Real `svchost.exe`/services don't live in `C:\Users\...`.
- `notepad.exe` has no business loading a custom DLL.

This is the implant.

---

## 6. Extracting the Implant from Memory

The first attempt (`--virtaddr` of the VAD start) returned nothing — the page isn't necessarily a `FILE_OBJECT`. So locate the file object through `filescan` and feed `dumpfiles` the actual offset:

```bash
python3 vol.py -f $MEM filescan 2>/dev/null \
  | grep -i "svchost.dll" > svchost_dll_offsets.txt

cat svchost_dll_offsets.txt
# 0xc78155e021e0  \Users\Mr_Togoo\svchost.dll

python3 vol.py -f $MEM -o $OUT windows.dumpfiles --virtaddr 0xc78155e021e0
```

That produced:

```
file.0xc78155e021e0.0xc78156ff3c70.ImageSectionObject.svchost.dll-1.img  (20 992 bytes)
```

While we were there, the dropper `svchost.exe` was also recovered from a parallel filescan:

```
file.0xc781564875f0.0xc7815465caa0.ImageSectionObject.svchost.exe-1.img  (49 152 bytes)
```

### Hashes for the artefacts

```
DLL  (svchost.dll)
  MD5    : 2599b77458cc5c2ef5231a3a7f9d0358
  SHA1   : 6c62e8a12458c3a49de0031ae0faaccbb8599369
  SHA256 : 92a500821718e29e0f0f9d5ba4963b373c0820a31f137643ca7bbd9970c49ffc

Dropper (svchost.exe)
  MD5    : 12a6dda976958d09879e8e1521ab1088
  SHA1   : be59a94f71db25f6d2d77b8573ff811a8b5debac
  SHA256 : 9ac21b43eb39b72657b619272dfe3974136efd8ce51cda93c4d1578f3817def2
```

---

## 7. Static Triage of `svchost.dll`

A Python sweep was run against the dump — direct flag regex, single-byte XOR brute force (keys 1..255), base64 decode, hex decode, and keyword extraction (`flag/csp/secret/key/togoo/b64/rot/…`).

**No flag**. The DLL doesn't carry the flag. But the strings table tells the entire story of what the implant does:

```
GitHubBackup/1.0
api.github.com
/repos/%s/releases/%s/assets?name=MyBackup.zip
Authorization: token %s
Content-Type: application/zip
Accept: application/vnd.github.v3+json
User-Agent: Windows-Update-Agent/10.0

[+] Starting backup for user: %s
C:\Users\%s\AppData\Local\Temp\sysbackup.zip
C:\Users\%s\Desktop
C:\Users\%s\Documents
C:\Users\%s\Downloads
[+] Backup file: %s

C:\Program Files\7-Zip\7z.exe
"C:\Program Files\7-Zip\7z.exe" a -tzip "%s" "%s\*" "%s\*" "%s\*"
      -p"Mr_Tog00_say_you" -mem=AES256 -mx5

[+] Uploading to GitHub...
[+] Upload successful!
[+] Cleanup complete

notepad.exe
[+] DLL loaded in notepad.exe
[+] Process ID: %lu
[+] In injector, attempting to inject into notepad...

ServerDyali/exfiltrate_data
github_pat_11BMLKGrfswqwqII03SppYFWULIwp_rgfswqeqwdw
```

Imports confirm the behaviour: `CreateToolhelp32Snapshot`, `Process32FirstW/NextW`, `OpenProcess`, `VirtualAllocEx`, `WriteProcessMemory`, `CreateRemoteThread` (classic remote-thread DLL injection); `InternetOpenA/HttpOpenRequestA/HttpSendRequestA` from `WININET.dll` (HTTP exfiltration).

Compiler fingerprint: `GCC: (Rev8, Built by MSYS2 project) 15.2.0` → built with MinGW-w64 / MSYS2.

### Reconstructed attack chain

1. **Dropper** `svchost.exe` finds (or starts) `notepad.exe`.
2. Resolves `notepad.exe`'s PID via `CreateToolhelp32Snapshot` + `Process32FirstW/NextW`.
3. Allocates memory in the remote process (`VirtualAllocEx`), writes `svchost.dll` (`WriteProcessMemory`), and spawns a thread there (`CreateRemoteThread`) that calls `LoadLibraryA`.
4. Inside `notepad.exe`, the DLL invokes 7-Zip with `-p"Mr_Tog00_say_you" -mem=AES256` to archive Desktop + Documents + Downloads into `%TEMP%\sysbackup.zip`.
5. Uploads the zip as a release asset to GitHub (`api.github.com/repos/.../releases/.../assets?name=MyBackup.zip`) with a hard-coded PAT, masquerading the User-Agent as `Windows-Update-Agent/10.0`.
6. Deletes the local zip (`[+] Cleanup complete`).

The dropper's strings reinforce this:

```
Host Process for Windows Services        ← masquerade banner
[*] Service Host starting...
[!] Target not found. Starting %ls...    ← if notepad isn't running
start notepad.exe
[+] System Component Loaded (PID: %lu)
```

> **Key insight.** The exfil archive name (`MyBackup.zip`) and per-folder targets are *exactly* the structure of the `MyBackup/` directory shipped with the challenge. The archive Mr. Togoo's malware uploaded **is** the dataset we have on disk. The flag has to live inside one of those documents.

---

## 8. Pivot to the Backup Archive

`windows.filescan` confirmed the user profile that was targeted:

```bash
python3 vol.py -f $MEM windows.filescan 2>/dev/null \
  | grep -i "Mr_Togoo" > mr_togoo_files.txt
```

The hit list is dominated by `\Users\Mr_Togoo\AppData\Local\Microsoft\Edge\...` and similar — i.e. a real user profile named `Mr_Togoo` existed on the box.

Then to the documents themselves:

```bash
cd ~/Desktop
ls -la MyBackup/Desktop MyBackup/Documents MyBackup/Downloads
```

### The first anomaly: size & timestamp drift

```
MyBackup/Desktop:
  -rwxrw-rw-  51044  Feb 11 01:44  Facture1.docx
  -rwxrw-rw-  51044  Feb 11 01:44  Facture2.docx
  -rwxrw-rw-  51044  Feb 11 01:44  Facture3.docx
  -rwxrw-rw-  51034  Feb 11 01:49  Facture4.docx   ← 10 bytes smaller, modified 5 min later
  -rwxrw-rw-  51044  Feb 11 01:44  Facture5.docx
  -rwxrw-rw-  51044  Feb 11 01:44  Facture6.docx
```

Every other document is identically 51 044 bytes and stamped at 01:44; **`Facture4.docx` is uniquely 51 034 bytes and stamped at 01:49**.

Cross-checking `docProps/core.xml`:

| File          | Revision | Modified            |
|---------------|----------|---------------------|
| Facture1–3,5,6 | 5        | 2026-02-11T00:44:00Z |
| **Facture4**  | **8**    | **2026-02-11T00:49:00Z** |

Same author/title/creator (`Sasha Bondereva`, `BENDALAA AYMANE`, "Sales invoice") across every file — Facture4 has just been revised more than the others.

### Confirming with payload-size

```bash
for f in MyBackup/**/*.docx; do
  unzip -l "$f" | tail -2
done
```

Every doc reports `216 201` total uncompressed bytes — **except Facture4 at `212 168`**. So content inside Facture4 has actually changed, not just the timestamp.

---

## 9. Pulling the Flag Out of `Facture4.docx`

The first scan focused on `word/document.xml`, `docProps/core.xml`, `docProps/app.xml` for direct `CSP{…}` — nothing. So we widened to "look for anything that looks suspicious in the visible text" — long base64 / hex / `flag` / `csp` patterns across the whole archive:

```bash
for f in MyBackup/Desktop/*.docx MyBackup/Documents/*.docx MyBackup/Downloads/*.docx; do
    text=$(unzip -p "$f" word/document.xml 2>/dev/null \
           | sed 's/<[^>]*>/ /g' | tr -s ' ')
    matches=$(echo "$text" | grep -oE \
       '[A-Za-z0-9+/=]{30,}|[0-9a-fA-F]{30,}|[Ff][Ll][Aa][Gg][^ ]*|[Cc][Ss][Pp][^ ]*' \
       | head -10)
    if [ -n "$matches" ]; then
        echo "--- $f ---"
        echo "$matches"
    fi
done
```

Out of 18 invoices, exactly one fires:

```
--- MyBackup/Desktop/Facture4.docx ---
Q1NQe1c0X1I0Ql9MMzRMMV9YNzRMXzM0UjQ5VDFONF80X0JST30=
```

The string starts with `Q1NQ` — the Base64 encoding of `CSP`. Decode it:

```bash
$ echo "Q1NQe1c0X1I0Ql9MMzRMMV9YNzRMXzM0UjQ5VDFONF80X0JST30=" | base64 -d
CSP{W4_R4B_L34L1_X74L_34R49T1N4_4_BRO}
```

---

## 10. Flag

```
CSP{W4_R4B_L34L1_X74L_34R49T1N4_4_BRO}
```

---

## 11. Indicators of Compromise (IoCs)

| Type         | Value                                                                                                       |
|--------------|-------------------------------------------------------------------------------------------------------------|
| File         | `C:\Users\Mr_Togoo\svchost.dll`                                                                              |
| File         | `C:\Users\<user>\AppData\Local\Temp\sysbackup.zip` (created, then cleaned up)                                |
| Process      | `notepad.exe` (PID 9152) loading `svchost.dll`                                                              |
| Process      | Rogue `svchost.exe` dropper (49 152 bytes) used as injector                                                 |
| Mutex / Hook | `CreateToolhelp32Snapshot` → `Process32FirstW/NextW` → `OpenProcess` → `VirtualAllocEx` → `CreateRemoteThread` |
| Tooling      | `C:\Program Files\7-Zip\7z.exe a -tzip ... -p"Mr_Tog00_say_you" -mem=AES256 -mx5`                            |
| Password     | `Mr_Tog00_say_you` (archive encryption)                                                                     |
| HTTP UA      | `Windows-Update-Agent/10.0`                                                                                 |
| C2 / Exfil   | `api.github.com/repos/<owner>/<repo>/releases/<id>/assets?name=MyBackup.zip`                                |
| C2 (alt)     | `ServerDyali/exfiltrate_data`                                                                               |
| Credential   | GitHub PAT: `github_pat_11BMLKGrfswqwqII03SppYFWULIwp_rgfswqeqwdw`                                          |
| Build env    | MinGW-w64 / `GCC (Rev8, Built by MSYS2 project) 15.2.0`                                                     |
| DLL SHA256   | `92a500821718e29e0f0f9d5ba4963b373c0820a31f137643ca7bbd9970c49ffc`                                          |
| EXE SHA256   | `9ac21b43eb39b72657b619272dfe3974136efd8ce51cda93c4d1578f3817def2`                                          |

---

## 12. Takeaways / Lessons Learned

- **Decoys are deliberate.** 179 `CSP{` hits in RAM, all fake — Mr. Togoo had searched the flag pattern in his browser to seed the image with noise. Always validate hits, never trust the first one.
- **`malfind` ≠ "no injection".** It only catches RWX / private-with-image-headers patterns. A DLL **loaded from disk** into the wrong process slides right past it — `vadinfo` with attention to *where* the file is backed from is what finds it.
- **Mismatched file paths are a giant flag.** A "`svchost.dll`" under `\Users\…\` is, by itself, near-conclusive.
- **Strings carry the entire story.** No reverse engineering was needed; the DLL leaked archive passwords, PATs, endpoints, and target paths in cleartext.
- **Look at the dataset, not just the dump.** The malware's purpose was to ship the documents off-host. The flag wasn't in memory because the malware never needed it in memory — it lived in one of the 18 archived documents, hidden as base64 inside `Facture4.docx`, distinguishable only by a 10-byte size delta and a later mtime.
- **Triage chain that worked here:** `memmap` → keyword sweep → `malfind` (negative) → `vadinfo` (positive) → `filescan` → `dumpfiles` → strings → disk-side artefact analysis.

---

## Appendix — Command Cheat-Sheet

```bash
# Identify processes / build a map
python3 vol.py -f $MEM windows.pslist
python3 vol.py -f $MEM windows.psscan
python3 vol.py -f $MEM windows.pstree

# Per-process full memory dump
python3 vol.py -f $MEM -o $OUT windows.memmap --pid <PID> --dump

# Injection hunters
python3 vol.py -f $MEM -o $OUT windows.malfind --pid <PID> --dump
python3 vol.py -f $MEM windows.vadinfo --pid <PID>

# File / object scanning
python3 vol.py -f $MEM windows.filescan
python3 vol.py -f $MEM -o $OUT windows.dumpfiles --virtaddr <PHYS_OFFSET>

# Raw keyword sweep (no Vol3 plugin needed)
grep -aoE "CSP\{[^}]+\}" memory.vmem
python3 -c "import re; data=open('memory.vmem','rb').read(); \
            print(len(re.findall(rb'C\\x00S\\x00P\\x00\\{\\x00', data)))"

# Triage a recovered PE
strings -n 6 svchost.dll | less
md5 svchost.dll; shasum -a 256 svchost.dll
```
