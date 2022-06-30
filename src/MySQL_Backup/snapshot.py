#!/usr/bin/python3
# -*- coding: utf-8 -*-
 
import os
 
class Snapshot:
  def __init__(self,config):
    self.config = config
    self.lvnmr = self.config.get('lvm','lvnmr')
    self.lvcreate = self.config.get('tools','lvcreate')
    self.backuplv = self.config.get('lvm','backuplv')
    self.vgname = self.config.get('lvm','vgname')
    self.lvname = self.config.get('lvm','lvname')
    self.mount = self.config.get('tools','mount')
    self.tmp = os.environ['HOME']
    self.mountdir = self.config.get('fs','mountdir')
 
 
  def create_lvm_snapshot(self):
    if self.lvnmr != "":
      command = self.lvcreate + "-s -l" + self.lvnmr + "--name=" + self.backuplv + "/dev/" + self.vgname + "/" + self.lvname
    else:
      command = self.lvcreate + "-s --size=" + self.lvsize + "--name=" + self.backuplv + "/dev/" + self.vgname + "/" + self.lvname
    return os.system(command)
 
  def mountsnap(self):
    params = "rw"
    if self.config.get('fs','xfs') == 1:
      params += ",nouuid"
    command = self.mount + " -o " + params + "/dev/" + self.vgname + "/" + self.backuplv + " " + self.mountdir
    return os.system(command)
 
  def mysql_recovery(self):
    command = "echo 'select 1;' | " + self.config.get('mysql','mysqld_safe') + " --user=mysql --socket=" + self.tmp + "/" + self.config.get('misc','recover_socket') + " --pid-file=" + self.config.get('misc','pidfile') + " --log-error=" + self.tmp + "/mysqlsnap_recoverserver.err --innodb-buffer-pool-size=3G --datadir=" + self.mountdir + "/" + self.config.get('fs','relpath') + "--skip-networking --skip-slave-start &";
    return os.system(command)
 