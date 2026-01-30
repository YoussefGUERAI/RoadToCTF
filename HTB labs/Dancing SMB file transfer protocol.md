There are multiple ways to transfer a file between two hosts (computers) on the same network. One of these protocols is studied in this example, and that is SMB (Server Message Block). This communication protocol provides shared access to files, printers, and serial ports between endpoints on a network. We mostly see SMB services running on Windows machines.

( by default on port port 445 TCP)

An SMB-enabled storage on the network is called a share . 
Our next step is to start enumerating the contents of the share found on our target in both cases. using smbclient :

smbclient -L (target_ip) : 

smbclient \\\\\\\\(target_ip)\\\\(Disk share) : to access the share then ( help ) to see the available commands 

