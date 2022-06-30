#!/usr/bin/python3
# -*- coding: utf-8 -*-

from settings import *
import os
import argparse
from mysql_enc_ini import Mysql_enc_ini
from configparser import ConfigParser
from analytics import Analytics
from migrate import Migrate
import mysql.connector
import datetime
from snapshot import *
import logging
import shutil
from os.path import exists as path_exists


class Bckp:
  def __init__(self,backuptype,config,logger,conn_data,dbh,**args):
    self.args = args
    self.backuptype = backuptype
    self.logger = logger
    self.conn_data = conn_data
    self.dbh = dbh
    self.config = config
    date = datetime.datetime.now()
    self.datum = date.strftime("%Y-%m-%d_%H-%M")
    self.purge_date = date.strftime("%Y-%m-%d %H:%M:%S")
    self.purge_cmd = "PURGE BINARY LOGS BEFORE '" + str(self.purge_date) +"'"
    my_list = str(self.config.get('mysql','dbserver')).split('.')
    self.server = my_list[0]

  def rsync(self):
    self.logger.info("Backing up using rsync")


  def rsnap(self):
    self.logger.info("Backing up using rsnap")


  def snapshot(self):
    self.logger.info("Backing up using snapshot")


  def tsm(self):
    self.logger.info("Backing up using tsm")


  def hotStandby(self):
    self.logger.info("Backing up using hotStandby")


  def mysqldump(self):
    if self.args["bckptyp"] == "full":
      if self.config.get('tools','mysqldump') != "":
        self.logger.info("Backing up using mysqldump")
        mysqldump = self.config.get('tools','mysqldump')
        results = {}

        mycursor = self.dbh.cursor()
        self.logger.info("Building mysqldump command line")
        dumpargs = "-h" + self.conn_data['host'] + " -u" + self.conn_data['user'] + " -P" + self.conn_data['port'] + " -p'" + self.conn_data['passwd'] + "'"
        sql = "show databases where `database` not in ('mysql','information_schema','performance_schema','sys');"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        for row in myresult:
          MySQLDump = mysqldump + "-aBc --create-options --add-drop-database --add-drop-table --verbose --routines --triggers --events --single-transaction --quick " + str(dumpargs) + " " + str(row[0]) + " > " + str(self.config.get('fs','backupdir')) + str(row[0]) + "_" + self.datum + ".sql"
          #results[row[0]] = os.system(MySQLDump)
          print(MySQLDump)
        self.log_backup()
        print(results)
        for key, res in results.items():
          print("Key: "+str(key)+"--Value: "+str(res))
          if res != 0:
            self.logger.error("An error occured during backup of DB: "+ key + ". please check your backup files under " +  str(self.config.get('fs','backupdir')))
          else:
            self.logger.info("Backup of DB: "+ key + " was succesful.")
        mycursor.close()
      else:
        print("mysqldump is not installed, please install package mysql-client")
    else:
      self.log_backup()

  def log_backup(self):
    self.logger.info("Backing up binlogs")
    mycursor = self.dbh.cursor()
    mycursor.execute("FLUSH BINARY LOGS")
    with open(self.config.get('mysql','log_bin_index'),'r') as bl:
      binlogs = bl.read().splitlines()
    bl.close()
    for binlog in binlogs:
      if self.args['debug'] == 1:
        print("binlog: " + str(binlog))
        print("Backuplog: " + str(self.config.get('fs','backuplog')))
        print("Log_bin_index: " + self.config.get('mysql','log_bin_index'))
      shutil.copy2(binlog,self.config.get('fs','backuplog'))
    print(self.purge_cmd)
    #mycursor.execute(self.purge_cmd)
    mycursor.close()



class MySQLBackup:
  def __init__(self,**args):
    self.args = args
    self.connect = Mysql_enc_ini(**self.args)
    self.config = ConfigParser()
    configfile = configfiledir + self.args["hostname"] + "_" + self.args["username"] + "_bckp.conf"
    if not path_exists(configfile):
      self.create_config(configfile)
    self.config.read(configfile)
    date = datetime.datetime.now()
    self.datum = date.strftime("%Y-%m-%d_%H-%M")
    self.dbserver = self.config.get('mysql','dbserver')
    self.debug = self.args['debug']
    my_list = str(self.dbserver).split('.')
    self.server = my_list[0]
    self.pwdfile = self.server + "_" + str(self.config.get('mysql','database')) + "_" + str(self.config.get('mysql','dbuser')) + ".pwd"
    self.conn_data = self.connect.decrypt(self.pwdfile)
    self.dbh = mysql.connector.connect(**self.conn_data)
    if not self.config.has_section('analytics'):
      Analytics(self.dbh,self.config)
      self.config.read(configfile)
    self.backuptype = self.config.get('misc','backuptype')
    logfile = self.config.get('logging','logfile') + "_" + self.config.get('mysql','dbserver') + "_" + self.config.get('mysql','database') + ".log"
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%d.%m.%Y %H:%M:%S')
    file_handler = logging.FileHandler(logfile, 'w+')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    self.logger.addHandler(file_handler)
    self.logger.info("Starting Backup on server " + self.dbserver + ": " + str(self.datum))
    self.bckp = Bckp(self.backuptype,self.config,self.logger,self.conn_data,self.dbh,**self.args)
    self.pidfile = self.config.get('misc','mysql_backup_pid')

  def run(self):
    if not path_exists(self.pidfile):
      with open(self.pidfile, 'w', encoding='utf-8') as pid:
        pid.write(str(os.getpid()))
        os.chmod(self.pidfile, 0o600)
        pid.close()
    else:
      print("Program already running - Stopping process")
      self.logger.error("Program already running - Stopping process")
      exit()
    snapshot = Snapshot(self.config)
    Migrate(self.dbh,self.config,self.logger)
    if self.backuptype == 'tar':
      pass
    elif self.backuptype == 'rsync':
      self.logger.info("Creating snapshot for rsync backup")
      if snapshot.create_lvm_snapshot() == 0:
        self.logger.info("Mounting snapshot")
        if snapshot.mountsnap() == 0:
          self.logger.info("DB recovery")
          if snapshot.mysql_recovery() == 0:
            self.bckp.rsync()
    elif self.backuptype == 'rsnap':
      self.logger.info("Creating snapshot for rsnap backup")
      if snapshot.create_lvm_snapshot() == 0:
        self.logger.info("Mounting snapshot")
        if snapshot.mountsnap() == 0:
          self.logger.info("DB recovery")
          if snapshot.mysql_recovery() == 0:
            self.bckp.rsnap()
    elif self.backuptype == 'snapshot':
      self.logger.info("Creating snapshot")
      if snapshot.create_lvm_snapshot() == 0:
        self.logger.info("Mounting snapshot")
        if snapshot.mountsnap() == 0:
          self.logger.info("DB recovery")
          if snapshot.mysql_recovery() == 0:
            self.bckp.snapshot()
    elif self.backuptype == 'tsm':
      self.logger.info("Creating snapshot for TSM backup")
      if snapshot.create_lvm_snapshot() == 0:
        self.logger.info("Mounting snapshot")
        if snapshot.mountsnap() == 0:
          self.logger.info("DB recovery")
          if snapshot.mysql_recovery() == 0:
            self.bckp.tsm()
    elif self.backuptype == 'hotStandBy':
      self.logger.info("Creating snapshot for hotStandby")
      if snapshot.create_lvm_snapshot() == 0:
        self.logger.info("Mounting snapshot")
        if snapshot.mountsnap() == 0:
          self.logger.info("DB recovery")
          if snapshot.mysql_recovery() == 0:
            self.bckp.hotStandby()
    else:
      self.bckp.mysqldump()
    self.dbh.close()
    os.remove(self.pidfile)

  def create_config(self,configfile):
    self.config.read_string(default_conf)
    mycnf = input("Give the location of the main my.cnf file: ")
    basisbackupdir = input("Give the destination of your backups (e. G. /backups/): ")
    print("Chose you backup type")
    for key, value in backup_type.items():
      print(key + "  - " + value)
    backuptype = input("Take your choice from the first row above, please consider installing the requirement: ")
    if self.args["username"] == "":
      self.args["username"] = input("Give the Database Username: ")
    self.config.set('mysql','mycnf',mycnf)
    self.config.set('mysql','dbuser',str(self.args["username"]))
    self.config.set('mysql','dbserver',str(self.args["hostname"]))
    self.config.set('fs','basisbackupdir',basisbackupdir)
    self.config.set('fs','backupdir',basisbackupdir + "mysql_backup/")
    self.config.set('fs','backuplog',basisbackupdir + "log/")
    self.config.set('fs','backupusr',basisbackupdir + "dump/")
    self.config.set('misc','configfiledir',configfiledir)
    self.config.set('misc','configfile', configfile)
    self.config.set('misc','backuptype',backuptype)
    print(configfile)
    fp=open(configfile,'w')
    self.config.write(fp)
    fp.close()

def args_list():
  parse = argparse.ArgumentParser('connect to mysql tools')
  parse.add_argument("-H","--host",dest='hostname',action='store',default='localhost',help='mysql server hostname.')
  parse.add_argument("-u","--user",dest='username',action='store',default='root',help='connect to mysql server user.')
  parse.add_argument("-d","--db",dest='database',action='store',default='mysql',help='Database name.')
  parse.add_argument("-P","--port",dest='port',action='store',default='3306',help='Port number.')
  parse.add_argument("-D","--debug",type=int,dest='debug',action='store',default=0,help='Debugging mode.')
  parse.add_argument("bckptyp",type=str,action='store',default='full',help='Full or log backup')
  args = parse.parse_args()
  return args

if __name__ == '__main__':
  kvargs = {}
  args = args_list()
  kvargs["hostname"] = args.hostname
  kvargs["username"] = args.username
  kvargs["database"] = args.database
  kvargs["debug"] = args.debug
  kvargs["port"] = args.port
  kvargs["bckptyp"] = args.bckptyp
  mybackup = MySQLBackup(**kvargs)
  mybackup.run()

