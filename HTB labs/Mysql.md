
### ✅ **1. Connect to a MySQL Server**

#### 🔸 Syntax:
`mysql -h <host> -u <username> -p`

#### 🔸 Example:

`mysql -h 10.129.246.117 -u root -p`

- `-h`: Host/IP of the MySQL server.
    
- `-u`: MySQL username.
    
- `-p`: Prompts for the password.
    

---

### ✅ **2. Basic MySQL Commands**

After logging in:

|Action|Command|
|---|---|
|🔍 Show all databases|`SHOW DATABASES;`|
|📂 Select a database|`USE database_name;`|
|📄 Show tables in the selected DB|`SHOW TABLES;`|
|📋 Show table structure|`DESCRIBE table_name;`|
|➕ Insert data into a table|`INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');`|
|🔎 Query data|`SELECT * FROM table_name;`|
|🛠️ Create a database|`CREATE DATABASE mydb;`|
|🧱 Create a table|`CREATE TABLE mytable (id INT PRIMARY KEY, name VARCHAR(100));`|
|🧹 Delete a database|`DROP DATABASE mydb;`|
|🚪 Exit MySQL|`exit;` or `quit;`|