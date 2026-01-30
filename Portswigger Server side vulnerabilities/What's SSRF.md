
Server-side request forgery is a web security vulnerability that allows an attacker to cause the server-side application to make requests to an unintended location.

![[Screenshot 2025-09-14 at 15.44.10.png]]

	the web application has its own internal network protected by the firewall, and other third party services / systems, but only permitted place to browse is the application itsef 

SSRF occurs when the user's got the ability to change the request made to the internal or external server / service and the the server doesn't properly validate the request.

## Key differences (why the diagram shows two boxes)

- **External/cloud service**
    - Public DNS name, publicly routable.
    - Requests leave the host and traverse the Internet.
    - Example: payment gateway, image CDN, external API.
        
- **Internal backend service**
    - Intended only for internal use by the application or ops staff.
    - Often protected by network segmentation, firewall rules, or simply bound to local interfaces.
    - Example: inventory microservice, admin panel, metadata service.
    - May be intentionally not exposed to the public Internet

**loopback = same host** (localhost); **private IP = other machine(s) on same LAN/virtual network**

## how does the attacker benefit from the admin panel when he's not authenticated ?

Notice that from the API request that allowed you to return the admin panel , that your exploitable endpoint , afterwards finding the right URL to do the service you wanna be doing , and paste it in that first endpoint that allowed you at first. 
For example :
1. Change the URL in the `stockApi` parameter to `http://localhost/admin`. This should display the administration interface.
2. Read the HTML to identify the URL to delete the target user, which is:
    `http://localhost/admin/delete?username=carlos`
3. Submit this URL in the `stockApi` parameter, to deliver the SSRF attack.

## SSRF attacks against other back-end systems

In some cases, the application server is able to interact with back-end systems that are not directly reachable by users. These systems often have non-routable private IP addresses. The back-end systems are normally protected by the network topology, so they often have a weaker security posture. In many cases, internal back-end systems contain sensitive functionality that can be accessed without authentication by anyone who is able to interact with the systems.

In the previous example, imagine there is an administrative interface at the back-end URL `https://192.168.0.68/admin`. An attacker can submit the following request to exploit the SSRF vulnerability, and access the administrative interface:

`POST /product/stock HTTP/1.0 Content-Type: application/x-www-form-urlencoded Content-Length: 118 stockApi=http://192.168.0.68/admin`

In this case you can use BurpSuite intruder in order to scan ranges of IP adresses and sort based on response length 