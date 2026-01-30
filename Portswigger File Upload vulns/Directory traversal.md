In some cases, the act of uploading the file is in itself enough to cause damage. Other attacks may involve a follow-up HTTP request for the file, typically to trigger its execution by the server.


## ! Content-Type :

The `Content-Type` response header may provide clues as to what kind of file the server thinks it has served. If this header hasn't been explicitly set by the application code, it normally contains the result of the file extension/MIME type mapping.

## Tip :
Web servers often use the `filename` field in `multipart/form-data` requests to determine the name and location where the file should be saved

## Lab 1 : Directory traversal 

1. **Multipart upload and the `filename=` field**
    
    - The multipart/form-data request contains a `Content-Disposition: form-data; name="avatar"; filename="..."` header.
        
    - Many servers use that `filename` _as provided_ when deciding where/how to save the uploaded file (or they pass it to application code which does the same).
        
2. **Simple upload (no traversal) — file saved under avatars/**
    
    - You uploaded `exploit.php` with a plain filename. The application stored it under `.../avatars/exploit.php` (or stored it as `avatars/exploit.php` and the application/handler returned the file contents).
        
    - The `/avatars` location in this lab was configured (intentionally or accidentally) so that `.php` files are **not** executed — they are served as static/plain text or read out by the application and returned raw. That is why an initial GET returned the PHP source instead of executing it. In other words: file present but not in a PHP-executable context.
        
3. **Attempt to use `../exploit.php` (literal traversal) — server strips it**
    
    - When you set `filename="../exploit.php"` the application sanitized/removed the `../` sequence (defense in place), so the resulting filename became `exploit.php` and the file ended up in the avatars folder again. No execution.
        
4. **Use URL-encoded traversal `..%2fexploit.php` to bypass naive filtering**
    
    - `%2f` is the percent-encoding for `/`. If the server or upload handling code **decodes percent-encoding** before validating/sanitizing the path component, the decoded value becomes `../exploit.php`.
        
    - In this lab the server **URL-decodes the filename** (or the multipart parser supplies a decoded value) _after_ the naive filter that only looked for literal `../` (or the filter only stripped literal `../` before decoding). So the filter didn’t catch `..%2f` and the decoded result contained a traversal sequence.




