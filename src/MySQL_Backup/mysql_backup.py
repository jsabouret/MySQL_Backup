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
import fnmatch
from os.path import exists as path_exists
from cleaning import Cleaner

class Bckp:
  def __init__(self,backuptype,config,logger,conn_data,dbh,**args):
    self.args = args
    self.backuptype = backuptype
    self.logger = logger
    self.conn_data = conn_data
    self.dbh = dbh
    self.config = config
    self.date = datetime.datetime.now()
    self.datum = self.date.strftime("%Y-%m-%d_%H-%M")
    self.purge_date = self.date.strftime("%Y-%m-%d %H:%M:%S")
    self.purge_cmd = "PURGE BINARY LOGS BEFORE '" + str(self.purge_date) +"'"
    my_list = str(self.config.get('mysql','dbserver')).split('.')
    self.server = my_list[0]

  def search_file(self,config,pitr,restoretype):
    datum = pitr.split()
    format = "%Y-%m-%d %H:%M:%S"
    format2 = "%Y-%m-%d %H-%M"
    pitr_dat = datetime.datetime.strptime(pitr, format)
    rest_files = []
    dbname = ""
    if restoretype == "database":
      dbname = input("You chose to restore only one database, please give the DB name: ")
      filename = dbname + "_" + datum[0] + "*.sql"
      bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
      for file in bckp_files:
        val = file.split("_")
        val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],format2)
        if val_dat <= pitr_dat:
          rest_files.append(file)
      #  Parsing Logs
      logdir = self.config.get('fs','backuplog') + "/log_" + datum[0]
      filename = self.config.get('mysql','log_basename')+ "*"
      log_files = self.find_files(filename,logdir)
      for file in log_files:
        rest_files.append(file)
    else:
      filename = self.config.get('mysql','dbserver') + "_user-" + self.datum[0] + "*sql"
      bckp_files = self.find_files(filename,str(self.config.get('fs','backupusr')))
      rest_files.append(bckp_files[-1])
      filename = "*_" + self.datum[0] + "*.sql"
      bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
      for file in bckp_files:
        if "cnf" not in file:
          filepath = os.path.split(file)
          dbname = filepath[1][0:-21]
          val = filepath[1][len(dbname):-1].split("_")
          if str(datum[0]) in file:
            val_dat = datetime.datetime.strptime(val[1] + " " + val[2].split(".")[0],format2)
            if val_dat <= pitr_dat:
              rest_files.append(file)  
      #  Parsing Logs
      logdir = filename,self.config.get('fs','backuplog') + "/log_" + self.datum[0]
      filename = self.config.get('mysql','log_basename') + "*"
      log_files = self.find_files(filename,logdir)
      for file in log_files:
        rest_files.append(file)
    return rest_files,dbname
  
  def find_files(self,filename,search_path):
    result = []
    search_path = str(search_path)
    for root, dir, files in os.walk(search_path):
      for name in files:
        if fnmatch.fnmatch(name, filename):
          result.append(os.path.join(root, name))
    return result

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

  def nobackup(self):
    pass

  def mysqldump(self):
    if self.args["bckptyp"] == "full":
      if self.config.get('tools','mysqldump') != "":
        self.logger.info("Backing up using mysqldump")
        mysqldump = str(self.config.get('tools','mysqldump'))
        results = {}

        mycursor = self.dbh.cursor()
        self.logger.info("Building mysqldump command line")
        dumpargs = "-h" + self.conn_data['host'] + " -u" + self.conn_data['user'] + " -P" + self.conn_data['port'] + " -p'" + self.conn_data['passwd'] + "'"
        sql = "show databases where `database` not in ('mysql','information_schema','performance_schema','sys');"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        for row in myresult:
          MySQLDump = mysqldump + " -aBc --create-options --add-drop-database --add-drop-table --verbose --routines --triggers --events --single-transaction --quick " + str(dumpargs) + " " + str(row[0]) + " > " + str(self.config.get('fs','backupdir')) + "/" +str(row[0]) + "_" + self.datum + ".sql"
          results[row[0]] = os.system(str(MySQLDump))
        self.log_backup()
        for key, res in results.items():
          if res != 0:
            self.logger.error("An error occured during backup of DB: "+ key + ". please check your backup files under " +  str(self.config.get('fs','backupdir')))
          else:
            self.logger.info("Backup of DB: "+ key + " was succesful.")
        mycursor.close()
      else:
        print("mysqldump is not installed, please install package mysql-client")
    elif self.args["bckptyp"] == "logs":
      self.log_backup()
    else:
      print("You probably misstyped the backup type, retry it!")
      self.logger.info("You probably misstyped the backup type, retry it!")
  
  def restore(self):
      rest_files = []
      print("Begin restore")
      rest_type = input("Please give the restore type wished, full or database: ")
      pitr = input("Give the point in time to restore to. (format: 2022-06-28 14:25:50): ")
      if rest_type == "full":
        service = input("PLease give the service name of your MySQL database. (mysql.service, mysqld.service or mysql@instance.service): ")
        self.logger.info("Trying to save the last logs if possible")
        print("Trying to save the last logs if possible")
        self.log_backup()
        self.logger.info("Stopping MySQL server")
        print("Stopping MySQL server")
        cmd = "systemctl stop " + service
        res = os.system(cmd)
        if res == 0:
          self.logger.info("MySQL is now stopped")
          print("MySQL is now stopped")
        else:
          self.logger.info("MySQL could not be stopped")
          resp = input("MySQL could not be stopped, please confirm any mysql processes are stoppped, once stopped or killed, answer: yes")
          if resp != "yes":
            self.logger.info("MySQL could not be stopped, aborting")
            print("MySQL could not be stopped, please try to kill any processes and restart the restore. ")
            exit(1)
        self.logger.info("Searching for the needed backup files")
        print("Searching for the needed backup files")
        rest_files,dbname = self.search_file(self.config,pitr,rest_type)
        self.logger.info("Starting restore of the full MySQL server")
        print("Starting restore of the full MySQL server")
        print("Search results")
        for file in rest_files:
          print("File: " + file)
        self.logger.info("Restarting MySQL server")
        print("Restarting MySQL server")
        cmd = "systemctl start " + service
        res = os.system(cmd)
      elif rest_type == "database":
        self.logger.info("Trying to save the last logs if possible")
        print("Trying to save the last logs if possible")
        self.log_backup()
        self.logger.info("Searching for the needed backup files")
        print("Searching for the needed backup files")
        rest_files,dbname = self.search_file(self.config,pitr,rest_type)
        self.logger.info("Starting restore of database" + dbname)
        print("Starting restore of database " + dbname)
        print("Search results")
        for file in rest_files:
          print("File: " + file)
      else:
        print("You probably misstype the restore type, please start over.")

  def log_backup(self):
    logdir = "log_" + self.date.strftime("%Y-%m-%d")
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
      logpath = self.config.get('fs','backuplog') + "/" + logdir
      if not path_exists(logpath):
        os.makedirs(logpath, exist_ok = True)
      shutil.copy2(binlog,logpath)
    mycursor.execute(self.purge_cmd)
    mycursor.close()
    self.logger.info("End of binlogs backup")

class MySQLBackup:
  def __init__(self,**args):
    self.args = args
    self.connect = Mysql_enc_ini(**self.args)
    self.config = ConfigParser()
    self.home = os.environ['HOME']
    configfile = configfiledir + "/" + self.args["hostname"] + "_" + self.args["username"] + "_bckp.conf"
    if not path_exists(configfile):
      self.create_config(configfile)
    self.config.read(configfile)
    date = datetime.datetime.now()
    self.datum = date.strftime("%Y-%m-%d_%H-%M")
    self.dbserver = self.config.get('mysql','dbserver')
    self.debug = self.args['debug']
    my_list = str(self.dbserver).split('.')
    self.server = my_list[0]
    self.pwdfile = self.home + "/" + self.server + "_" + str(self.config.get('mysql','database')) + "_" + str(self.config.get('mysql','dbuser')) + ".pwd"
    self.conn_data = self.connect.decrypt(self.pwdfile)
    self.dbh = mysql.connector.connect(**self.conn_data)
    if not self.config.has_section('analytics'):
      Analytics(self.dbh,self.config)
      self.config.read(configfile)
    self.backuptype = self.config.get('misc','backuptype')
    logfile = self.config.get('logging','logfile') + self.config.get('mysql','dbserver') + "_" + self.config.get('mysql','database') + "_" + self.args["bckptyp"] + ".log"
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
      print("Program already running - Stopping process. If you're sure that the program is not running, Erase file: " + str(self.pidfile))
      self.logger.error("Program already running - Stopping process")
      exit()
    if self.args["bckptyp"] == "logs":
      self.bckp.log_backup()
    elif self.args["bckptyp"] == "full":
      snapshot = Snapshot(self.config)
      Migrate(self.dbh,self.config,self.logger)
      if self.backuptype == 'nobackup':
        pass
      elif self.backuptype == 'tar':
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
    else:
      self.bckp.restore()
    date = datetime.datetime.now()
    self.datum = date.strftime("%Y-%m-%d_%H-%M")
    if self.args["bckptyp"] == "full":
      Cleaner(self.config,self.logger,self.backuptype)
    self.logger.info("End of Backup on server " + self.dbserver + ": " + str(self.datum))
    self.dbh.close()
    os.remove(self.pidfile)

  def create_config(self,configfile):
    self.config.read_string(default_conf)
    mycnf = input("Give the location of the main my.cnf file: ")
    basisbackupdir = input("Give the destination of your backups (e. G. /backups): ")
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
    self.config.set('fs','backupdir',basisbackupdir + "/mysql_backup")
    self.config.set('fs','backuplog',basisbackupdir + "/log")
    self.config.set('fs','backupusr',basisbackupdir + "/dump")
    self.config.set('misc','configfiledir',configfiledir)
    self.config.set('misc','configfile', configfile)
    self.config.set('misc','backuptype',backuptype)
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
  parse.add_argument("bckptyp",type=str,action='store',default='full',help='Full or logs backup, restore')
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

