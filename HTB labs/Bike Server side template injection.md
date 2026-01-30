Wappalyzer extension to know the web frameworks and servvers used on the web page.

What is a Template Engine? Template Engines are used to display dynamically generated content on a web page. They replace the variables inside a template file with actual values and display these values to the client (i.e. a user opening a page through their browser).

## what's an SSTi ??

To put it plainly an SSTI is an exploitation technique where the attacker injects native (to the Template Engine) code into a web page. The code is then run via the Template Engine and the attacker gains code execution on the affected server. This attack is very common on Node.js websites and there is a good possibility that a Template Engine is being used to reflect the email that the user inputs in the contact field.

## Hacktricks website for Payloads !!

Payload used after recognising the template server ; 

![[Screenshot 2025-06-12 at 17.57.26.png]]

an error gets sent back stating that the require function isn't a global variable ; 
Now we have to find a solution to use this function and that is by seeing the node.js documentation we can then see :

Taking a closer look at the documentation we see that there is a #process object available. The documentation states that this object provides information about, and control over, the current Node.js process. We might be able to use this object to load a module.
{{this.push "return process.mainModule.require('child_process').execSync('whoami');"}}
we can now find the require function and use it 
