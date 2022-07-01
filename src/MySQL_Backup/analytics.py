#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from settings import *
import shutil
from os.path import exists as path_exists
import re

class Analytics():
  def __init__(self,dbh,config):
    self.dbh = dbh
    self.mycursor = self.dbh.cursor()
    self.config = config
    self.sections = ['fs','misc','logging']
    self.keys = {'fs':('mountdir','backupdir','backuplog','backupusr'),'misc':('destsrvdir','hooksdir','configfiledir','mysql_backup_pid'),'logging':('logdir',)}
    self.dirs = []

    sql = "SHOW VARIABLES"
    self.mycursor.execute(sql)
    self.myresults = self.mycursor.fetchall()
    if not self.config.has_section('mycnf'):
      self.config.add_section('mycnf')
    for result in self.myresults:
      self.config.set('mycnf',result[0],result[1])
    if self.config.get('mycnf','log_bin') == 'ON':
      filepath = os.path.split(self.config.get('mycnf','log_bin_index'))
      if filepath[0] == "":
        dblogs = self.config.get('mycnf','datadir')
        log_bin_index = dblogs + "/" + self.config.get('mycnf','log_bin_index')
      else:
        dblogs = filepath[0]
        log_bin_index = self.config.get('mycnf','log_bin_index')
      self.config.set('mysql','dblogs',dblogs)
      self.config.set('mysql','log_bin_index',log_bin_index)
    if self.config.get('mycnf','log_error') != 'stderr':
      filepath = os.path.split(self.config.get('mycnf','log_error'))
      self.config.set('logging','logdir',filepath[0])
      self.config.set('logging','logfile',filepath[0] + '/backup_')
    else:
      self.config.set('logging','logdir','var/log/mysql')
      self.config.set('logging','logfile',self.config.get('logging','logdir') + '/backup_')
    self.config.set('mysql','dbdata',self.config.get('mycnf','datadir'))
    self.dirs.append(self.config.get('mysql','dbdata'))
    for cmd in cmds:
      path_to_cmd = shutil.which(cmd)
      if path_to_cmd != None:
        self.config.set('tools',cmd,path_to_cmd)
      else:
        self.config.set('tools',cmd,"")
    # Gathering LVM information
    myvgs = self.vggroups(mountsfile,self.dirs)
    if any(myvgs):
      self.config.set('lvm','vgname',myvgs[self.dirs[0]]["vgname"])
      self.config.set('lvm','lvname',myvgs[self.dirs[0]]["lvname"])
    #self.config.add_section('analytics')
    #self.config.set('analytics','status','done')
    fp=open(self.config.get('misc','configfile'),'w')
    self.config.write(fp)
    fp.close()
    self.mycursor.close()
    ##  Creating working diretories
    ct = 0
    self.dirs = []
    for section in self.sections:
      length = len(self.keys[section])
      if length > 0:
        while ct < length:
          self.dirs.append(config.get(section,self.keys[section][ct]))
          ct += 1
        ct = 0
      else:
        self.dirs.append(config.get(section,self.keys[section]))
    print(self.dirs)
    for dir in self.dirs:
      filepath = os.path.split(dir)
      if filepath[0] != "":
        if not path_exists(filepath[0]):
          os.makedirs(filepath[0])

  def grep(self,line,regex_pattern):
    pattern = re.compile(regex_pattern)
    if pattern.search(line):
      return 0
    else:
      return 1

  def unique(self,list):
    list_of_unique_values = []
    unique_values = set(list)
    for value in unique_values:
      list_of_unique_values.append(value)
    return list_of_unique_values

  def vggroups(self,mountsfile,dirs):
    res = {}
    flag = 0
    for dir in dirs:
      res[dir] = {}

    with open(mountsfile, "r") as mnt:
      mounts = mnt.read().splitlines()
    mnt.close()
    for mnt in mounts:
      for dir in dirs:
        if self.grep(mnt,dir) == 0:
          if self.grep(mnt,"vg") == 0:
            lines = mnt.split()
            flag = 1
            res[dir]["vgname"] = lines[0].split("/")[3].split("-")[0]
            res[dir]["lvname"] = lines[0].split("/")[3].split("-")[1]
    if flag == 0:
      res = {}
    return res
