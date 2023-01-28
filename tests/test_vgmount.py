#!/usr/bin/python3
# -*- coding: utf-8 -*-

from settings import *
from configparser import ConfigParser
from snapshot import *

configfile = "/etc/mysql_root_bckp.conf"
config = ConfigParser()
config.read(configfile)
snapshot = Snapshot(config)
if snapshot.create_lvm_snapshot() == 0:
  print("Mounting snapshot")
  if snapshot.mountsnap() == 0:
    print("Snap mounted")