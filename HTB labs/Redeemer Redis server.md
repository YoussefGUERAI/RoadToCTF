
Port Scanning : 
use -p- to scan all ports in this case the port number is very big it doesn't appear on a default nmap scan

Redis Server command-line : 
connect to the redis server :  redis-cli -h (target_ip)
enumerate infos on the db : info

![[Screenshot 2025-06-09 at 03.27.52.png]]

shows the number of databases 
to enter a db : select (index)
list all keys in the db :  keys *
see the value of a given key : get (key)
