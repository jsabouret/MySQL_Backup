#!/usr/bin/python3
# -*- coding: utf-8 -*-

from settings import *
import datetime
from os.path import exists as path_exists
import os
import shutil

class Migrate:
  def __init__(self,dbh,config,logger):
    self.dbh = dbh
    self.config = config
    self.logger = logger
    bckp2keep = 15
    x = datetime.datetime.now()
    datum = x.strftime("%Y-%m-%d_%H-%M")
    bckp_dir = self.config.get('fs','backupusr')
    file = bckp_dir + '/' + self.config.get('mysql','dbserver') + '_user-' + datum + '.sql'
    self.logger.info("Backing up my.cnf file")
    if path_exists(self.config.get('mysql','mycnf')):
      shutil.copy2(self.config.get('mysql','mycnf'),self.config.get('fs','backupdir'))
    f = open(file, "w")
    mycursor=self.dbh.cursor()
    mycursor2=self.dbh.cursor()
    mycursor3=self.dbh.cursor()
    mycursor.execute("SELECT CAST(schema_name as CHAR(100)) FROM information_schema.schemata order by 1")
    myresult = mycursor.fetchall()
    for row in myresult:
      if row[0] != 'information_schema' or row[0] != 'mysql' or row[0] != 'performance_schema' or row[0] == 'sys':
        sql = "CREATE DATABASE /*!32312 IF NOT EXISTS*/ " + str(row[0]) + " /*!40100 DEFAULT CHARACTER SET utf8mb4 */;\n"
        f.write(sql)
    sql = "SELECT user, host FROM mysql.user"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    for row in myresult:
      if row[1] != "" or row[1] != "%":
        sql2 = "show create user %s@%s"
        sql3 = "SHOW GRANTS FOR %s@%s"
        mycursor2.execute(sql2,(row[0],row[1]))
        myresult2 = mycursor2.fetchall()
        for row2 in myresult2:
          f.write(row2[0] + ";\n")
        mycursor3.execute(sql3,(row[0],row[1]))
        myresult3 = mycursor3.fetchall()
        for row2 in myresult3:
          f.write(row2[0] + ";\n")
      else:
        sql2 = "show create user %s"
        sql3 = "SHOW GRANTS FOR %s"
        mycursor2.execute(sql2,row[0])
        myresult2 = mycursor2.fetchall()
        for row2 in myresult2:
          f.write(row2[0] + ";\n")
        mycursor3.execute(sql3,row[0])
        myresult3 = mycursor3.fetchall()
        for row2 in myresult3:
          f.write(row2[0] + ";\n")
    mycursor.close()
    mycursor2.close()
    mycursor3.close()
    f.close()
    #### File cleaning ######
    self.logger.info("Purging user account backup files older than " + str(bckp2keep) + " days")
    cmd = "find " + bckp_dir + " -name \"user*sql\" -mtime +" + str(bckp2keep) + " -delete"
    os.system(cmd)
