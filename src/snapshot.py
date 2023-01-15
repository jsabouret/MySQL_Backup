#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import ctypes
import ctypes.util
import shutil

class Snapshot:
  def __init__(self,config):
    self.config = config
    self.lvnmr = self.config.get('lvm','lvnmr')
    self.lvcreate = self.config.get('tools','lvcreate')
    self.lvremove = self.config.get('tools','lvremove')
    self.backuplv = self.config.get('lvm','backuplv')
    self.vgname = self.config.get('lvm','vgname')
    self.lvname = self.config.get('lvm','lvname')
    self.mount = self.config.get('tools','mount')
    self.tmp = "/tmp/mysql_backup"
    self.mountdir = self.config.get('fs','mountdir')
    self.lvsize = self.config.get('lvm','lvsize')
    self.libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
    self.libc.mount.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p)
 
  def create_lvm_snapshot(self):
    if self.lvnmr != "":
      command = self.lvcreate + " -s -l" + self.lvnmr + " --name=" + self.backuplv + " /dev/" + self.vgname + "/" + self.lvname
    else:
      command = self.lvcreate + " -s --size=" + self.lvsize + " --name=" + self.backuplv + " /dev/" + self.vgname + "/" + self.lvname
    return os.system(command)

  def destroy_lvm_snapshot(self):
    command = self.lvremove + " -f " " /dev/" + self.vgname + "/" + self.backuplv
    return os.system(command)

  def mountsnap(self):
    params = ""
    lv = "/dev/" + self.vgname + "/" + self.backuplv
    if self.config.get('lvm','fs') == "xfs":
      params += ",nouuid"
    shutil.chown(self.mountdir,"mysql","mysql")
    ret = self.libc.mount(lv.encode(), self.mountdir.encode(), self.config.get('lvm','fs').encode(), 0, params.encode())
    if ret < 0:
      errno = ctypes.get_errno()
      raise OSError(errno, f"Error mounting {lv} ({self.config.get('lvm','fs')}) on {self.mountdir} with options '{params}': {os.strerror(errno)}")
    return ret
  
  def umount(self,target):
    command = "umount " + str(target)
    return os.system(command)

  def mysql_recovery(self):
    command = "echo 'select 1;' | " + self.config.get('mysql','mysqld_safe') + " --user=mysql --socket=" + self.tmp + "/" + self.config.get('misc','recover_socket') + " --pid-file=" + self.config.get('misc','pidfile') + " --log-error=" + self.tmp + "/mysqlsnap_recoverserver.err --innodb-buffer-pool-size=3G --datadir=" + self.mountdir + "/" + self.config.get('fs','relpath') + " --skip-networking --skip-slave-start &";
    return os.system(command)

  def rollback(self,srclv,snapshot):
    if self.umount(srclv) == 0:
      command = "lvconvert --merge " + snapshot
      if os.system(command) == 0:
        os.system("mount -a")
      return 0
    else:
      print("Directory " + srclv + " cannot be unmounted, please do it manually")
      return 1
