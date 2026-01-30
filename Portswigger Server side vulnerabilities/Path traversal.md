### 🖥️ What a web server really is

- At the end of the day, a “server” is just a **computer** (like your laptop) but configured to **respond to requests from the internet**.
    
- It has:
    
    - An **operating system** (Linux, Windows, etc.)
        
    - A **filesystem** (folders and files)
        
    - **Programs running** (like Apache, Nginx, PHP, Node.js) that handle requests.
        

---

### 📂 Where webpages live

On Linux web servers, the default place where web files live is usually:

`/var/www/`

This directory is like the "public folder" of the server:

- Inside it you might see:
    
    - `/var/www/html/` → the root website (what shows up when you visit the homepage).
        
    - `/var/www/images/` → a folder for image files.
        
    - `/var/www/app/` → maybe the source code of a web app.
        

So when you visit:

`http://example.com/index.html`

The server looks in:

`/var/www/html/index.html`

and sends that file to your browser.