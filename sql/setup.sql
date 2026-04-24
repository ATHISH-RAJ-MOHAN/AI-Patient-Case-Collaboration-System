-- Drop User if already exist
DROP USER IF EXISTS 'chatuser'@'localhost';
DROP USER IF EXISTS 'chatuser'@'127.0.0.1';
FLUSH PRIVILEGES;

-- Drop Database of already exist
DROP DATABASE IF EXISTS healthcare_group_chat;

-- create database
CREATE database healthcare_group_chat 
character SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- create new user (not root)
create user 'chatuser'@'localhost' IDENTIFIED BY 'chatpass';
create user 'chatuser'@'127.0.0.1' IDENTIFIED BY 'chatpass';

-- grant all privilages for the user (update, drop, delete, insert) to this database
GRANT ALL PRIVILEGES ON healthcare_group_chat.* to 'chatuser'@'localhost';
GRANT ALL PRIVILEGES ON healthcare_group_chat.* to 'chatuser'@'127.0.0.1';
FLUSH PRIVILEGES;

USE healthcare_group_chat;

-- verify
select user from mysql.user;

-- verify access
show databases;
