Memory challenges answer one core question: **“What was running, what did it do, and how did it hide?”**


## Why Profiles Exist (The Problem)

Every OS version has:

- Different kernel structures
- Different offsets in memory
- Different data layouts

Example:

- Windows 7 ≠ Windows 10
- Linux 5.4 ≠ Linux 6.1

Memory is just **raw bytes**.  
Volatility needs to know **what those bytes mean**.

Syntax: `python3 vol.py -f <file> windows.info`

 `pslist`: 
 The output from this plugin will include all current processes and terminated processes with their exit times.

`psscan`:
To combat this evasion technique, we can use `psscan`;this technique of listing processes will locate processes by finding data structures that match `_EPROCESS`. While this technique can help with evasion countermeasures, it can also cause false positives.


# 🧠 What Is `malfind`?

`malfind` looks for **executable code in memory that should not be executable**.

## `windows.memmap` DOES:

- Enumerate **Virtual Address Descriptors (VADs)** for a process
- Show:
    
    - Every virtual memory region
    - Permissions
    - Backing type

- Optionally **dump the raw bytes** of those regions

When malware (or any program) makes an HTTP request, this happens:

1. Program builds a request string in memory:
    
    `GET /gate.php HTTP/1.1 Host: 41.168.5.140 User-Agent: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1)`
    
2. This string lives in:
    
    - Heap memory
    - Or a dynamically allocated buffer
    
3. That buffer is passed to:
    
    - `WinInet`
    - `WinHTTP`
    - `WSA*` socket APIs
        
4. Kernel copies it to network buffers
    
5. Data is transmitted
    

🧠 **Memory is the birthplace of HTTP traffic** ( All requests can still live in memory RAM until overriden so they can be relevant to SOC) 

`vol.py -f <dump> -o /dir/to/store_dump/ windows.memmap.Memmap --pid <suspicious PID> --dump

Once the dump is stored use: `strings *.dmp | grep -i "user-agent" `

## .dlllist : 

| Field | Meaning                                      |
| ----- | -------------------------------------------- |
| Base  | Where the module is mapped in virtual memory |
| Size  | Size of the mapped image                     |
| Name  | Full path on disk                            |
### 🔹 Full executable path

You get **disk-backed truth**, not just process name.

### 🔹 Detect DLL injection

- Unknown DLLs
- DLLs loaded from temp directories
- DLLs loaded from user-writable paths


## 🧠 Analyst-Level Correlation (IMPORTANT)

### `dlllist` tells you:

> “What code is loaded into this process?”

### `handles` tells you:

> “What this process is touching or controlling?”


