#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
from settings import *
import datetime


file = "/backups/mysql2/mysql_backup/db_inventory_2022-07-06_00-00.sql"
#file = "//backups/mysql2/mysql_backup/backup_2022-07-06_00-00.sql"
pitr = "2022-07-06 15:00:00"
datum = pitr.split()
print(datum)
format = "%Y-%m-%d %H:%M:%S"
format2 = "%Y-%m-%d %H-%M"
pitr_dat = datetime.datetime.strptime(pitr, format)
rest_files = []

if "cnf" not in file:
  filepath = os.path.split(file)
  dbname = filepath[1][0:-21]
  print(dbname)
  val = filepath[1][len(dbname):-1].split("_")
  print(val)
  if str(datum[0]) in file:
    val_dat = datetime.datetime.strptime(val[1] + " " + val[2].split(".")[0],format2)
    if val_dat <= pitr_dat:
      print("File: " + file)
      rest_files.append(file)
