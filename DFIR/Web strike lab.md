# Identify malicious upload / web shell

### **Technique**

Focus on POST requests from attacker IP.

### **Filters**

`ip.src == <attacker_ip> && http.request.method == "POST" http.request.method == "POST" tcp contains "filename"`


---

#  Identify the upload directory

### **Technique**

Look at server responses (301, 302) and redirected paths.

### **Filters**

`http.response.code == 301 || http.response.code == 302 http.request.uri contains "upload"`

---

# ✅  Find commands executed through the reverse shell

### **Technique**

Use **Follow → TCP Stream** on the reverse shell connection.

### **Filters**

`tcp.dstport == <attacker_port> tcp.stream eq <stream_number>`

### **Steps**

- Identify stream (`tcp.stream`)
    
- Follow each one to read commands (ls, cat, curl, etc.)
    

---

# ✅ **7. Detect the exfiltrated file**

### **Technique**

Look for `curl -X POST`, `wget`, or `nc` commands.