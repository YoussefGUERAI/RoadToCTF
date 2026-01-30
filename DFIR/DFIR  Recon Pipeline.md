# 🔥 **1. Firewall Logs — `firewall.log`**

### **What information they give you**

Firewall logs show **network traffic that is allowed or blocked** based on security rules.

### **Key things you can learn**

- **Source IP** and **destination IP**
    
- **Ports** involved (e.g., 22, 80, 443)
    
- **Protocol** (TCP, UDP, ICMP…)
    
- Whether the traffic was **ALLOWED** or **BLOCKED**
    
- Possible **scanning attempts**, e.g. many ports probed by same IP
    
- Suspicious inbound/outbound connections
    
- Attempts to reach **forbidden services** (SSH, RDP, etc.)

---

# 🛡️ **2. IDS / WAF Logs — `ids_alerts.log`**

This usually contains alerts from an **Intrusion Detection System** or **Web Application Firewall**.

### **What information they give you**

These logs show attempts to exploit **web vulnerabilities** or perform **malicious activities** on web servers.

### **Key things you can learn**

- **Detected attacks**, such as:
    
    - SQL injection attempts
        
    - XSS
        
    - File upload abuse
        
    - Command injection
        
    - Directory traversal
        
- Severity of alerts
    
- Source IP triggering the alert
    
- URL or endpoint targeted
    
- Rule/signature that was triggered
    
---

# 🔐 **3. VPN Authentication Logs — `vpn_auth.log`**

These logs record attempts to authenticate into the corporate VPN.

### **What information they give you**

- Username attempting login
    
- Login success or failure
    
- Source IP of login attempt
    
- Timestamps of each authentication event
    
- Disconnections / session durations
    

### **Key things you can learn**

- Whether an attacker attempted **credential stuffing** or **brute force**
    
- Whether a stolen password was used successfully
    
- Login from **unusual countries or IP ranges**
    
- The timeline of **remote access to the network**
    