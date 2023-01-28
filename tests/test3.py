#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import ctypes
import ctypes.util
import shutil
from configparser import ConfigParser
from snapshot import Snapshot

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

snapshot = Snapshot(config)

print("Creating snapshot for borg backup")
if snapshot.create_lvm_snapshot() == 0:
  print("Mounting snapshot")
  if snapshot.mountsnap() == 0:
    print("DB recovery")
    if snapshot.mysql_recovery() == 0:
      print("Finished")
    if snapshot.umount(mountdir) == 0:
      print("snapshot unmounted!")
      if snapshot.destroy_lvm_snapshot() == 0:
        print("logical volume destroyed")

