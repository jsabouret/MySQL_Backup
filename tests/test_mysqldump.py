#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from configparser import ConfigParser
from mysql_enc_ini import Mysql_enc_ini
import mysql.connector
import datetime
from time import sleep

config = ConfigParser()
configfile = "/etc/mysql2_root_bckp.conf"
home = os.environ['HOME']
config.read(configfile)
connect = Mysql_enc_ini()
pwdfile = home + "/.mysql2_mysql_" + str(config.get('mysql','dbuser')) + ".pwd" 
conn_data = connect.decrypt(pwdfile)
dbh = mysql.connector.connect(**conn_data)
mycursor = dbh.cursor(dictionary=True)
mysqldump = str(config.get('tools','mysqldump'))
results = {}
date = datetime.datetime.now()
datum = date.strftime("%Y-%m-%d_%H-%M")
mycursor = dbh.cursor()
dumpargs = "-h" + conn_data['host'] + " -u" + conn_data['user'] + " -P" + conn_data['port'] + " -p'" + conn_data['passwd'] + "'"
sql = "show databases where `database` not in ('mysql','information_schema','performance_schema','sys');"
mycursor.execute(sql)
myresult = mycursor.fetchall()
for row in myresult:
  MySQLDump = mysqldump + " -aBc --no-data --create-options --add-drop-database --add-drop-table --verbose --routines --triggers --events --single-transaction --quick " + str(dumpargs) + " " + str(row[0]) + " > " + str(config.get('fs','backupdir')) + "/" +str(row[0]) + "_" + datum + ".sql"
  print(str(MySQLDump))
  results[row[0]] = os.system(str(MySQLDump))

