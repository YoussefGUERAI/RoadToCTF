as a difference between authorization and authentication : Authentication is the process of verifying that a user is who they claim to be. Authorization involves verifying whether a user is allowed to do something.

## Burp Suite Intruder 

Burp Suite is a toolkit for web app security testing, and **Intruder** is one of its modules.  
Intruder is basically an **automated request repeater/fuzzer**.

Usernames Wordlist : /usr/share/wordlists/dirb/commun.txt 
Passwords Wordlist : /usr/share/wordlists/fasttrack.txt

![[Screenshot 2025-09-14 at 14.27.39.png]]

Usually Intruder is very slow and can be replaced with tools like hydra or ffuf for enumeration but still a good tool to check different server responses and sort based on length or status code

## 2FA Authentification 

Sometimes, you are already logged in without actually enter the verification code, So if you know the page you ll be redirected to , entering that page manually to the URL will be sufficient.

## URI / URL 
A URL (Uniform Resource Locator) is a specific type of URI (Uniform Resource Identifier) that not only identifies a resource but also specifies its location on a network and the method for retrieving it,**Status codes**:
- `200 OK` — success
- `201 Created` — resource created
- `204 No Content` — success but no body
- `400 Bad Request` — client error
- `401 Unauthorized` — missing/invalid auth
- `403 Forbidden` — no permission
- `404 Not Found` — no such resource
- `429 Too Many Requests` — rate-limited
- `500` etc — server error

