
First things first, starting by scanning the ports , only the http port 80 is working.
Then, using gobuster for enumerating the the different server's directories.
Once done, we can see that the /dev contains some php files that lead to a /phpbash.php which is sortf of a web shell.
The user's flag can be easilly obtained by navigating to arrexel's home directory.
Using the command sudo -l : **The `sudo -l` command is used to list the commands that the current user is allowed (or forbidden) to run with elevated privileges on the current host.**


![[Screenshot 2025-09-16 at 20.08.52.png]]

using this privilege we can escalate to the scripts directory where we can find : 
![[Screenshot 2025-09-16 at 20.10.29.png]]
As we can see the root is running the **test.py** file every couple of minutes, which sounds intriguing .

### 🧩 What’s the Goal?!
- The attacker has found or uploaded a file called **`phpbash.php`** on the target server.
    
- This gives them **remote command execution** as the web server user — typically `www-data`.
    
- The attacker wants to **get a proper shell** they can interact with easily — what we call a **TTY shell** (pseudo-terminal).


