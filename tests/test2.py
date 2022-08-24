#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import ctypes
import ctypes.util
import shutil
from configparser import ConfigParser

config = ConfigParser()
configfile = "/etc/mysql2_root_bckp.conf"
home = os.environ['HOME']
config.read(configfile)

lvnmr = config.get('lvm','lvnmr')
lvcreate = config.get('tools','lvcreate')
backuplv = config.get('lvm','backuplv')
lvremove = config.get('tools','lvremove')
vgname = config.get('lvm','vgname')
lvname = config.get('lvm','lvname')
mount = config.get('tools','mount')
tmp = "/tmp/mysql_backup"
mountdir = config.get('fs','mountdir')
lvsize = config.get('lvm','lvsize')
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
libc.mount.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p)


def create_lvm_snapshot():
  if lvnmr != "":
    command = lvcreate + " -s -l" + lvnmr + " --name=" + backuplv + " /dev/" + vgname + "/" + lvname
  else:
    command = lvcreate + " -s --size=" + lvsize + " --name=" + backuplv + " /dev/" + vgname + "/" + lvname
  return os.system(command)

def destroy_lvm_snapshot():
  command = lvremove + " -f " " /dev/" + vgname + "/" + backuplv
  print(command)
  return os.system(command)

def mount(source, target, fs, options=''):
  ret = libc.mount(source.encode(), target.encode(), fs.encode(), 0, options.encode())
  if ret < 0:
    errno = ctypes.get_errno()
    raise OSError(errno, f"Error mounting {source} ({fs}) on {target} with options '{options}': {os.strerror(errno)}")
    print("https://chyoa.com/chapter/Please-don%E2%80%99t-tease-me.629725")
  return ret

def umount(target):
  command = "umount " + str(target)
  return os.system(command)

def mountsnap():
  params = "rw"
  lv = "/dev/" + vgname + "/" + backuplv
  if config.get('lvm','fs') == "xfs":
    params += ",nouuid"
  res = mount(lv, mountdir, config.get('lvm','fs'), params)
  shutil.chown(mountdir,"mysql","mysql")
  return res
 
def mysql_recovery():
  command = "echo 'select 1;' | " + config.get('mysql','mysqld_safe') + " --user=mysql --socket=" + tmp + "/" + config.get('misc','recover_socket') + " --pid-file=" + config.get('misc','pidfile') + " --log-error=" + tmp + "/mysqlsnap_recoverserver.err --innodb-buffer-pool-size=3G --datadir=" + mountdir + "/" + config.get('fs','relpath') + " --skip-networking --skip-slave-start &";
  return os.system(command)
 







print("Creating snapshot for borg backup")
if create_lvm_snapshot() == 0:
  print("Mounting snapshot")
  if mountsnap() == 0:
    print("DB recovery")
    if mysql_recovery() == 0:
      print("Finished")
    if umount(mountdir) == 0:
      print("snapshot unmounted!")
      if destroy_lvm_snapshot() == 0:
        print("logical volume destroyed")
