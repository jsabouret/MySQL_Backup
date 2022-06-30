#!/usr/bin/python3
# -*- coding: utf-8 -*-

import psutil
import re

dirs = ["dbdata","dblogs"]
mountsfile = "/proc/mounts"
test = {
  "dbdata": {"vg": "datavg", "lv": "lvdata"},
  "dblogs": {"vg": "datavg", "lv": "lvlogs"}
}
print(test)
for key,value in test.items():
  for key2,value2 in value.items:
    print("Dir " + str(key) + " ist auf " +str(key2) + ": " + str(value2))

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

def vggroups(mountsfile,dirs):
  res = {}

  with open(mountsfile, "r") as mnt:
    mounts = mnt.read().splitlines()
  mnt.close()
  for mnt in mounts:
    for dir in dirs:
      if grep(mnt,dir) == 0:
        if grep(mnt,"vg") == 0:
          lines = mnt.split()
          print(dirs)
          print(lines)
          print(lines[0].split("/")[3].split("-")[0])
          print(lines[0].split("/")[3].split("-")[1])
          print(dir)
          print(res)
          #res.update({dir: "vg"}) = lines[0].split("/")[3].split("-")[0]
          #res[dir]["lv"] = lines[0].split("/")[3].split("-")[1]
  return res

for dir in dirs:

  print(dir)
myvgs = vggroups(mountsfile,dirs)
for key,value in myvgs.items():
    print("Dir " + str(key) + " ist auf VG: " + str(value))

