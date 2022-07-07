#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from settings import *
import fnmatch
import datetime
from configparser import ConfigParser

sections = ['fs','misc','logging']
keys = {'fs':('mountdir','backupdir','backuplog','backupusr'),'misc':('destsrvdir','hooksdir','configfiledir','mysql_backup_pid'),'logging':('logdir',)}
dirs = []
  



########################################

def find_files(filename, search_path):
  result = []
  for root, dir, files in os.walk(search_path):
    for name in files:
      if fnmatch.fnmatch(name, filename):
        result.append(os.path.join(root, name))
  return result

def search_file(pitr,restoretype,config):
    datum = pitr.split()
    format = "%Y-%m-%d %H:%M:%S"
    format2 = "%Y-%m-%d %H-%M"
    pitr_dat = datetime.datetime.strptime(pitr, format)
    rest_files = []
    dbname = ""
    if restoretype == "database":
      dbname = input("You chose to restore only one database, please give the DB name: ")
      filename = dbname + "_" + datum[0] + "*.sql"
      bckp_files = find_files(filename,config.get('fs','backupdir'))
      for file in bckp_files:
        print(file)
        val = file.split("_")
        val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],format2)
        if val_dat <= pitr_dat:
          rest_files.append(file)
      #  Parsing Logs
      logdir = config.get('fs','backuplog') + "/log_" + datum[0]
      print("Logdir: " + logdir)
      filename = config.get('mysql','log_basename')+ "*"
      print("Filename: " + filename)
      log_files = find_files(filename,logdir)
      for file in log_files:
        print("File: " + file)
        rest_files.append(file)
    else:
      filename = config.get('mysql','dbserver') + "_user-" + datum[0] + "*sql"
      bckp_files = find_files(filename,str(config.get('fs','backupusr')))
      rest_files.append(bckp_files[-1])
      filename = "*_" + datum[0] + "*.sql"
      bckp_files = find_files(filename,config.get('fs','backupdir'))
      for file in bckp_files:
        val = file.split("_")
        val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],format2)
        if val_dat >= pitr_dat:
          print("File: " + file)
          rest_files.append(file)
      #  Parsing Logs
      logdir = filename,config.get('fs','backupdir') + "/log_" + datum[0]
      filename = config.get('mysql','log_basename') + "*"
      log_files = find_files(filename,logdir)
      for file in log_files:
        rest_files.append(file)
      print("Search results")
      for file in rest_files:
        print("File: " + file)
    print("Return values")
    return rest_files,dbname
  

########################################
pitr = "2022-07-06 15:00:00"
config = ConfigParser()
configfile = "/etc/mysql2_root_bckp.conf"
config.read(configfile)
bckp_files,dbname = search_file(pitr, "database",config)
## zfssnap_2022-07-06_00-00.sql
for file in bckp_files:
  print(file)



