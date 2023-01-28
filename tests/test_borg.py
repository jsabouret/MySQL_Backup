#!/usr/bin/python3
# -*- coding: utf-8 -*-

from borgbackup import BorgBackup
import sys
import logging
from settings import *
from mysql_enc_ini import Mysql_enc_ini
from configparser import ConfigParser
import subprocess
import os
import datetime

kvargs = {}
kvargs["host"] = "mysql2"
kvargs["user"] = "root"
kvargs["database"] = "mysql"
kvargs["debug"] = 0
kvargs["port"] = "3306"
kvargs["bckptyp"] = "full"
logfile = "borgbackup.log"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
config = ConfigParser()
home = os.environ['HOME']
configfile = "/etc/mysql2_root_bckp.conf"
config.read(configfile)
connect = Mysql_enc_ini(**kvargs)
pwdfile = home + "/mysql2_" + str(config.get('mysql','database')) + "_" + str(config.get('mysql','dbuser')) + ".pwd"
conn_data = connect.decrypt(pwdfile)
os.environ['BORG_PASSPHRASE'] = conn_data["passwd"]
os.environ['BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'] = "yes"
os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = "yes"
flag = 0
my_list = str(config.get('mysql','dbserver')).split('.')
server = my_list[0]
pitr = "2022-08-24 10:00:00"
datum = pitr.split()

bckp_name = server + "_borg_" + str(datum[0])

borg = BorgBackup(config)
code, out, err = borg.borgList(config.get('fs','borgdir'))
res = out.decode("utf-8")
res = res.split()
for item in res:
  if (item.find(bckp_name)) != -1:
    flag = 1
    bckp_name = item
    print ('Found at ', bckp_name)
if flag != 1:
  print("No corresponding Backup found for this PITR")
print("err: '{}'".format(err))
print("exit: {}".format(code))
