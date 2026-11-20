@echo off
C:\xampp\mysql\bin\mysql.exe -u root --password= -e "DROP DATABASE IF EXISTS livraria; CREATE DATABASE livraria CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
C:\xampp\mysql\bin\mysql.exe -u root --password= < schema_mysql.sql