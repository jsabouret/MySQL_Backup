#!/usr/bin/python3
# -*- coding: utf-8 -*-

import psutil
import re

dirs = ["/dbdata","/dblogs"]
mountsfile = "/proc/mounts"

def grep(line,regex_pattern):
  pattern = re.compile(regex_pattern)
  if pattern.search(line):
    return 0
  else:
    return 1

def unique(list):
  list_of_unique_values = []
  unique_values = set(list)
  for value in unique_values:
    list_of_unique_values.append(value)
  return list_of_unique_values


def unique(list):
  list_of_unique_values = []
  unique_values = set(list)
  for value in unique_values:
    list_of_unique_values.append(value)
  return list_of_unique_values

def vggroups(mountsfile,dirs):
    res = {}
    flag = 0
    for dir in dirs:
      res[dir] = {}

    with open(mountsfile, "r") as mnt:
      mounts = mnt.read().splitlines()
    mnt.close()
    for mnt in mounts:
      print("mnt1: " + mnt)
      for dir in dirs:
        if grep(mnt,dir) == 0:
          print("mnt2: " + mnt)
          if grep(mnt,"vg") == 0:
            print("mnt3: " + mnt)
            lines = mnt.split()
            flag = 1
            res[dir]["vgname"] = lines[0].split("/")[3].split("-")[0]
            res[dir]["lvname"] = lines[0].split("/")[3].split("-")[1]
            res[dir]['fs'] = lines[2]
    if flag == 0:
      res = {}
    print(f'res')
    return res

myvgs = vggroups(mountsfile,dirs)
#for key,value in myvgs.items():
#    print("Dir " + str(key) + " ist auf VG: " + str(value))
for key,value in myvgs.items():
  for key2 in value:
    print("Dir " + str(key) + " ist auf " +str(key2) + ": " + str(value[key2]) + " mit filesystem " + myvgs[key]["fs"])


