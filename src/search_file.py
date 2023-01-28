#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from settings import *
import fnmatch
import datetime

class Search_file:
  def __init__(self,config,pitr,restoretype):
    self.config = config
    self.pitr = pitr
    self.restoretype = restoretype
    self.datum = pitr.split()
    format = "%Y-%m-%d %H:%M:%S"
    format2 = "%Y-%m-%d %H-%M"
    pitr_dat = datetime.datetime.strptime(pitr, format)
    self.rest_files = []
    self.dbname = ""
    if self.restoretype == "database":
      self.dbname = input("You chose to restore only one database, please give the DB name: ")
      filename = self.dbname + "_" + self.datum[0] + "*.sql"
      bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
      for file in bckp_files:
        val = file.split("_")
        val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],format2)
        if val_dat >= pitr_dat:
          self.rest_files.append(file)
      #  Parsing Logs
      logdir = self.config.get('fs','backupdir') + "/log_" + self.datum[0]
      filename = self.config.get('mysql','log_basename')+ "*"
      log_files = self.find_files(filename,logdir)
      for file in log_files:
        self.rest_files.append(file)
    else:
      filename = self.config.get('mysql','dbserver') + "_user-" + self.datum[0] + "*sql"
      bckp_files = self.find_files(filename,str(self.config.get('fs','backupusr')))
      self.rest_files.append(bckp_files[-1])
      filename = "*_" + self.datum[0] + "*.sql"
      bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
      for file in bckp_files:
        val = file.split("_")
        val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],format2)
        if val_dat >= pitr_dat:
          self.rest_files.append(file)
      #  Parsing Logs
      logdir = filename,self.config.get('fs','backupdir') + "/log_" + self.datum[0]
      filename = self.config.get('mysql','log_basename') + "*"
      log_files = self.find_files(filename,logdir)
      for file in log_files:
        self.rest_files.append(file)
    return list(self.rest_files),self.dbname
    

  def find_files(self,filename,search_path):
    result = []
    search_path = str(search_path)
    print("Filename: " + filename)
    print("Dir: " + search_path)
    for root, dir, files in os.walk(search_path):
      for name in files:
        if fnmatch.fnmatch(name, filename):
          result.append(os.path.join(root, name))
    return result