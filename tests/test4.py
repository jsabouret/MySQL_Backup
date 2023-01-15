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
pwdfile = home + "/mysql2_abstund_" + str(config.get('mysql','dbuser')) + ".pwd" 
conn_data = connect.decrypt(pwdfile)
dbh = mysql.connector.connect(**conn_data)
mycursor = dbh.cursor(dictionary=True)

while True:
  date = datetime.datetime.now()
  datum = date.strftime("%Y-%m-%d %H:%M:%S")
  sql = "insert into time_bandit (stamp) values ('" + str(datum) + "');"
  mycursor.execute(sql)
  dbh.commit()
  sleep(5)

mycursor.close()
dbh.close()
