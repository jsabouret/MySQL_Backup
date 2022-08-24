#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from glob import glob
from pathlib import Path

class Cleaner:
  def __init__(self,config,logger,bckptyp):
    self.config = config
    self.logger = logger
    self.bckptyp = bckptyp
    self.bckp2keep = self.config.get('misc','backup2keep')
    

    # Cleaning user infos
    #### File cleaning ######
    bckp_dir = self.config.get('fs','backupusr')
    self.logger.info("Purging user account backup files older than " + str(self.bckp2keep) + " days")
    cmd = "find " + bckp_dir + " -name \"" + self.config.get('mysql','dbserver') + "_user*sql\" -mtime +" + str(self.bckp2keep) + " -delete"
    os.system(cmd)

    # Cleaning mysqldump backups
    if self.bckptyp == "mysqldump":
      backupdir = self.config.get('fs','backupdir')
      backuplog = self.config.get('fs','backuplog')
      self.logger.info("Purging mysqldump backup files and logs older than " + str(self.bckp2keep) + " days")
      cmd = "find " + backupdir + " -mtime +" + str(self.bckp2keep) + " -delete"
      os.system(cmd)
    elif self.bckptyp == "borg":
      pass

    # Cleaning empty diretories under log
    self.logger.info("Cleaning log directories and erase the empty one.")
    backuplog = self.config.get('fs','backuplog')
    cmd = "find " + backuplog + " -name \"*mysql-bin*\" -mtime +" + str(self.bckp2keep) + " -delete"
    os.system(cmd)
    dirs = [f.path for f in os.scandir(backuplog) if f.is_dir()]
    for dir in dirs:
      if len(os.listdir(dir)) == 0:
        cmd = "rm -rf " + dir
        os.system(cmd)