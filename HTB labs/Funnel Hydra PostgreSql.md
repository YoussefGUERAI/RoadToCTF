d
## Use Hydra to bruteforce users :

hydra -L users.txt -p 'P@ssw0rd123' ssh://target.com'

- `-L users.txt`: List of usernames.
    
- `-p 'P@ssw0rd123'`: The known password.
    
- `ssh://target.com`: The SSH service and host.
## socket statistics 

A crucial command at this point in time is the ss command, which stands for socket statistics , and can be used to check which ports are listening locally on a given machine.
ss -tln

-l: Display only listening sockets.
-t: Display TCP sockets.
-n: Do not try to resolve service names.![[Screenshot 2025-06-11 at 03.08.24.png]]
![[Screenshot 2025-06-11 at 03.09.48.png]]

## PSQL commands 

	psql -U christine -h localhost -p 1234

to start interacting with the target machine's postgresql service ;

\list : to list the different databases
\connect db : connect to the desired database 
\dt to see the database schema 

then simple SELECT * FROM flag;



## PSQL Server Example : 

### Connect to the psql server :

i0ussef-picoctf@webshell:~$ psql -h saturn.picoctf.net -p 58787 -U postgres pico
Password for user postgres: 
psql (14.17 (Ubuntu 14.17-0ubuntu0.22.04.1), server 15.2 (Debian 15.2-1.pgdg110+1))
WARNING: psql major version 14, server major version 15.
         Some psql features might not work.
Type "help" for help.
### List the different databases : pico=# \list


                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges   
-----------+----------+----------+------------+------------+-----------------------
 pico      | postgres | UTF8     | en_US.utf8 | en_US.utf8 | 
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 | 
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 | =c/postgres          +
           |          |          |            |            | postgres=CTc/postgres
(4 rows)

### Access the pico db : pico=# \connect pico 

pico=# \connect pico 
psql (14.17 (Ubuntu 14.17-0ubuntu0.22.04.1), server 15.2 (Debian 15.2-1.pgdg110+1))
WARNING: psql major version 14, server major version 15.
         Some psql features might not work.
You are now connected to database "pico" as user "postgres".
pico=# \dt
         List of relations
 Schema | Name  | Type  |  Owner   
--------+-------+-------+----------
 public | flags | table | postgres
(1 row)

### Access the flags table :  pico=# \d flags

pico=# \d flags
                        Table "public.flags"
  Column   |          Type          | Collation | Nullable | Default 
-----------+------------------------+-----------+----------+---------
 id        | integer                |           | not null | 
 firstname | character varying(255) |           |          | 
 lastname  | character varying(255) |           |          | 
 address   | character varying(255) |           |          | 
Indexes:
    "flags_pkey" PRIMARY KEY, btree (id)

pico=# SELECT * FROM flags
pico-# SELECT * FROM flags;
`error explanation : you accidentally pressed Enter after the first line, so `psql` thought you were continuing the same command.  
That’s why your prompt changed from:
`pico=#`
to:
`pico-#`

(the `-` means it’s waiting for more input to complete a previous command).
Then, when you typed `SELECT * FROM flags;`, it got appended to an **unfinished command**, leading to the error. 

## Querying the flags table :  SELECT * FROM flags;

pico=# SELECT * FROM flags;
 id | firstname | lastname  |                address                 
----+-----------+-----------+----------------------------------------
  1 | Luke      | Skywalker | picoCTF{L3arN_S0m3_5qL_t0d4Y_21c94904}
  2 | Leia      | Organa    | Alderaan
  3 | Han       | Solo      | Corellia
(3 rows)

pico=# 