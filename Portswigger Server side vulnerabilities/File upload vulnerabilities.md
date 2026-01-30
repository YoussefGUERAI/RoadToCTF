#### Web shell
A web shell is a malicious script that enables an attacker to execute arbitrary commands on a remote web server simply by sending HTTP requests to the right endpoint.

For example, the following PHP one-liner could be used to read arbitrary files from the server's filesystem:
`<?php echo file_get_contents('/path/to/target/file'); ?>`

This script enables you to pass an arbitrary system command via a query parameter as follows:
`<?php echo system($_GET['command']); ?>`
`GET /example/exploit.php?command=id HTTP/1.1`


## How is the web shell triggered 

**Upload into a web-accessible location**
    - If the app saves the file under the site’s document root (e.g. `/var/www/html/uploads/shell.php`), requesting `https://example.com/uploads/shell.php` makes the server fetch that file.
    - If the server has a handler for `.php`, it passes the file to the PHP interpreter and the code runs.


## Flawed file type validation

basically, in an html form , using a POST request with the Content-type header as : application/x-www-form-url-encoded,
but for bigger chunks of binary data , eg uploading images we may specify the header by : multipart/form-data

A basic example with a form uploading multiple data with different sizes :

![[Screenshot 2025-09-15 at 21.24.11.png]]

 One way that websites may attempt to validate file uploads is to check that this input-specific `Content-Type` header matches an expected MIME type. And that can be bypassed using tools like Burp Suite Intruder 

For example , in this case in the original request as the content-type of the file i sent was text/php , but as seen in the **Accept** header , it's not listed as a permitted type ; 
One way to solve the issue was to just change that text/php to image/jpeg and that worked in this case ;

![[Screenshot 2025-09-15 at 21.37.47.png]]