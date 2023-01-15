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
import subprocess
from snapshot import *
import logging
import shutil
import sys
import re
import fnmatch
from os.path import exists as path_exists
from cleaning import Cleaner
from borgbackup import BorgBackup
from cryptography.fernet import Fernet

class Bckp:
  def __init__(self,backuptype,config,logger,conn_data,dbh,pidfile,**args):
    self.args = args
    self.backuptype = backuptype
    self.logger = logger
    self.pidfile = pidfile
    self.home = os.environ['HOME']
    self.conn_data = conn_data
    self.decrypted_file = self.home + '/decrypted_' + str(os.getpid()) + '.ini'
    self.key_file = self.home + '/.mclef'
    self.dbh = dbh
    self.config = config
    self.mountdir = self.config.get('fs','mountdir')
    self.encrypted_inifile = self.home + "/.borgbackup_passwd.pwd"
    self.date = datetime.datetime.now()
    self.datum = self.date.strftime("%Y-%m-%d_%H-%M")
    self.purge_date = self.date.strftime("%Y-%m-%d %H:%M:%S")
    self.purge_cmd = "PURGE BINARY LOGS BEFORE '" + str(self.purge_date) +"'"
    self.format = "%Y-%m-%d %H:%M:%S"
    self.format2 = "%Y-%m-%d %H-%M"
    my_list = str(self.config.get('mysql','dbserver')).split('.')
    self.server = my_list[0]
    self.patrn = "Dump completed"
    with open(self.key_file, 'rb') as file:
      key = file.read()
      file.close
      self.key = key

  def search_file(self,config,pitr,restoretype,bckptype):
    datum = pitr.split()
    pitr_dat = datetime.datetime.strptime(pitr, self.format)
    rest_files = []
    rest_path = []
    starttimes = {}
    dbname = ""
    if bckptype == "mysqldump":
      if restoretype == "database":
        dbname = input("You chose to restore only one database, please give the DB name: ")
        filename = dbname + "_" + datum[0] + "*.sql"
        bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
        for file in bckp_files:
          val = file.split("_")
          val_dat = datetime.datetime.strptime(val[2] + " " + val[3].split(".")[0],self.format2)
          if val_dat <= pitr_dat:
            rest_files.append(file)
            file_one = open(file, "r")
            for line in file_one:
              if re.search(self.patrn, line):
                starttimes[file] = str(line.split()[4]) + " " + str(line.split()[5])
        #  Parsing Logs
        logdir = self.config.get('fs','backuplog') + "/log_" + datum[0]
        filename = self.config.get('mysql','log_basename')+ "*"
        log_files = self.find_files(filename,logdir)
        for file in log_files:
          rest_files.append(file)
      else:
        filename = self.config.get('mysql','dbserver') + "_user-" + datum[0] + "*sql"
        bckp_files = self.find_files(filename,str(self.config.get('fs','backupusr')))
        rest_files.append(bckp_files[-1])
        filename = "*_" + datum[0] + "*.sql"
        bckp_files = self.find_files(filename,self.config.get('fs','backupdir'))
        for file in bckp_files:
          if "cnf" not in file:
            filepath = os.path.split(file)
            dbname = filepath[1][0:-21]
            val = filepath[1][len(dbname):-1].split("_")
            if str(datum[0]) in file:
              val_dat = datetime.datetime.strptime(val[1] + " " + val[2].split(".")[0],self.format2)
              if val_dat <= pitr_dat:
                rest_files.append(file)
                file_one = open(file, "r")
                for line in file_one:
                  if re.search(self.patrn, line):
                    starttimes[file] = (str(line.split()[4]) + " " + str(line.split()[5]))
          else:
            if path_exists(file) == "False":
              shutil.copy2(file,"/etc/")
        #  Parsing Logs
        logdir = self.config.get('fs','backuplog') + "/log_" + datum[0]
        filename = self.config.get('mysql','log_basename')+ "*"
        log_files = self.find_files(filename,logdir)
        for file in log_files:
          rest_files.append(file)
    elif bckptype == "borg":
      if restoretype == "database":
        dbname = input("You chose to restore only one database, please give the DB name: ")
        rest_path.append(self.config.get('fs','mountdir')+"/"+dbname)
        logdir = self.config.get('fs','backuplog') + "/log_" + datum[0]
        filename = self.config.get('mysql','log_basename')+ "*"
        log_files = self.find_files(filename,logdir)
        for file in log_files:
          rest_files.append(file)
      else:
        logdir = self.config.get('fs','backuplog') + "/log_" + datum[0]
        filename = self.config.get('mysql','log_basename')+ "*"
        log_files = self.find_files(filename,logdir)
        for file in log_files:
          rest_files.append(file)
    return rest_files,rest_path,dbname,starttimes
  
  def find_files(self,filename,search_path):
    result = []
    search_path = str(search_path)
    for root, dir, files in os.walk(search_path):
      for name in files:
        if fnmatch.fnmatch(name, filename):
          result.append(os.path.join(root, name))
    return result

  def borg(self):
    bckp_dirs = []
    excludes = []

    if self.config.get('borg','usage') == "yes":
      self.logger.info("Backing up using borg")
      borg = BorgBackup(self.config)
      fernet = Fernet(self.key)
      if self.config.get('borg','init') != "done":
        self.logger.info(self.config.get('fs','borgdir') + " is not a valid repository. Creating one!")
        os.environ['BORG_PASSPHRASE'] = self.conn_data["passwd"]
        os.environ['BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'] = "yes"
        os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = "yes"
        res = borg.borginit(self.config.get('fs','borgdir'))
        if res == 0:
          parser = ConfigParser()
          parser.add_section('borgbackup')
          parser.set('borgbackup', 'passwd', str(self.conn_data["passwd"]))
          fp=open(self.decrypted_file,'w')
          parser.write(fp)
          fp.close()
          with open(self.decrypted_file, 'rb') as file:
            original = file.read()
          os.remove(self.decrypted_file)
          encrypted = fernet.encrypt(original)
          with open (self.encrypted_inifile, 'wb') as file:
            file.write(encrypted)
            os.chmod(self.encrypted_inifile, 0o600)
          borg.getkey(self.config.get('fs','borgdir'))
          print("Your Password: "+ str(self.conn_data["passwd"]))
      else:
        self.logger.info(self.config.get('fs','borgdir') + " is a valid repository.")
      with open(self.encrypted_inifile, 'rb') as encrypted_inifile:
        encrypted = encrypted_inifile.read()
      decrypted = fernet.decrypt(encrypted)
      with open(self.decrypted_file, 'wb') as decrypted_file:
        decrypted_file.write(decrypted)
      config = ConfigParser()
      config.read(self.decrypted_file)
      os.remove(self.decrypted_file)
      os.environ['BORG_PASSPHRASE'] = config.get('borgbackup', 'passwd')
      os.environ['BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'] = "yes"
      os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = "yes"
      self.log_backup()
      bckp_name = self.server + "_borg_" + str(self.date.strftime("%Y-%m-%d"))
      bckp_dirs.append(self.home)
      bckp_dirs.append(self.mountdir)
      bckp_dirs.append(self.config.get('fs','backuplog'))
      bckp_dirs.append(self.config.get('fs','backupusr'))
      code, out, err = borg.borgBackup(self.config.get('fs','borgdir'),bckp_name,bckp_dirs,excludes)
      res = out.decode("utf-8")
      res = res.split()
      self.logger.info(res)
      print(format(err))
    else:
      self.logger.info("BorgBackup is not allowed or not installed!")

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
  
  def runCmd(self,cmd):
    proc = subprocess.Popen(cmd,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr

  def restore(self):
    fernet = Fernet(self.key)
    rest_files = []
    rest_path = []
    flag = 0
    if self.config.get('misc','backuptype') == "mysqldump":
      self.logger.info("Begin restore")
      print("Begin restore")
      rest_type = input("Please give the restore type wished, full or database: ")
      pitr = input("Give the point in time to restore to. (format: 2022-06-28 14:25:50): ")
      if rest_type == "full":
        service = input("PLease give the service name of your MySQL database. (mysql.service, mysqld.service or mysql@instance.service): ")
        if self.dbh != "False":
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
        rest_files,rest_path,dbname,starttimes = self.search_file(self.config,pitr,rest_type,self.config.get('misc','backuptype'))
        MySQL_Binlog = self.config.get('tools','mysqlbinlog') + " --no-defaults --stop-datetime=\"" + pitr + "\" "
        self.logger.info("Starting restore of the full MySQL server")
        print("Starting restore of the full MySQL server")
        cmd = "rm -rf " + self.config.get('mysql','dbdata') + "/*"
        os.system(cmd)
        if self.config.get('mysql','dblogs') != "":
          cmd = "rm -rf " + self.config.get('mysql','dblogs') + "/*"
          os.system(cmd)
        shutil.copy2(str(self.config.get('mycnf','log_error')),str(self.config.get('mycnf','log_error')+"_restore"))
        os.system("> " + str(self.config.get('mycnf','log_error')))
        self.logger.info("Restarting MySQL server")
        print("Restarting MySQL server")
        cmd = "systemctl start " + service
        res = os.system(cmd)
        if res == 0:
          self.logger.info("MySQL server restarted")
          print("MySQL server restarted")
        else:
          self.logger.info("MySQL could not be started")
          resp = input("MySQL could not be started, please check the error log, correct any error and restart the serverc, once started, answer: yes")
          if resp != "yes":
            self.logger.info("MySQL could not be started, aborting")
            print("MySQL could not be started, please check the error log, correct any error and restart the restore. ")
            exit(1)
        cmd = "grep '.*temporary password.*' " + str(self.config.get('mycnf','log_error')) + " | awk '{print $13}' | sed 's/ //g' | tr -dc '[[:print:]]'  > /tmp/pwd"
        if os.system(cmd) == 0:
          with open("/tmp/pwd", "r") as pwd:
            passwd = pwd.read()
        sql = "alter user 'root'@'localhost' identified by \'" + str(self.conn_data["passwd"]) + "\';"
        cmd = "echo \"" + sql + "\" | mysql -s -u" + self.conn_data["user"] + " --connect-expired-password -p\'" + passwd + "\'"
        os.system(cmd)
        sql = "grant all privileges on *.* to 'root'@'localhost' with grant option;"
        cmd = "echo \"" + sql + "\" | mysql -s -u" + self.conn_data["user"] + " --connect-expired-password -p\'" + str(self.conn_data["passwd"]) + "\'"
        os.system(cmd)
        for file in rest_files:
          if "mysql_backup" in file or "user" in file:
            cmd = "mysql -s -u" + self.conn_data["user"] + " -p\'" + self.conn_data["passwd"] + "\' < " + file
            os.system(cmd)
          else:
            MySQL_Binlog += file + " "
        MySQL_Binlog += "> binlogs"
        os.system(MySQL_Binlog)
        print("Starting recovery")
        self.logger.info("Starting recovery")
        cmd = "mysql -s -u" + self.conn_data["user"] + " -p" + self.conn_data["passwd"] + " < binlogs"
        os.system(cmd)
      elif rest_type == "database":
        self.logger.info("Trying to save the last logs if possible")
        print("Trying to save the last logs if possible")
        self.log_backup()
        self.logger.info("Searching for the needed backup files")
        print("Searching for the needed backup files")
        rest_files,rest_path,dbname,starttimes = self.search_file(self.config,pitr,rest_type,self.config.get('misc','backuptype'))
        self.logger.info("Starting restore of database" + dbname)
        print("Starting restore of database " + dbname)
        for file in rest_files:
          MySQL_Binlog = self.config.get('tools','mysqlbinlog') + " --no-defaults --database=" + dbname + " --start-datetime=\"" + starttimes[file] + "\" --stop-datetime=\"" + pitr + "\" "
          if "mysql_backup" in file:
            cmd = "mysql -s -u" + self.conn_data["user"] + " -p" + self.conn_data["passwd"] + " < " + file
            os.system(cmd)
          else:
            MySQL_Binlog += file + " "
        MySQL_Binlog += "> binlogs"
        print(MySQL_Binlog)
        os.system(MySQL_Binlog)
        print("Starting recovery")
        self.logger.info("Starting recovery")
        cmd = "mysql -s -u" + self.conn_data["user"] + " -p" + self.conn_data["passwd"] + " < binlogs"
        os.system(cmd)
      else:
        print("You probably misstype the restore type, please start over.")
    elif self.config.get('misc','backuptype') == "borg":
      with open(self.encrypted_inifile, 'rb') as encrypted_inifile:
        encrypted = encrypted_inifile.read()
      decrypted = fernet.decrypt(encrypted)
      with open(self.decrypted_file, 'wb') as decrypted_file:
        decrypted_file.write(decrypted)
      config = ConfigParser()
      snapshot = Snapshot(self.config)
      config.read(self.decrypted_file)
      os.remove(self.decrypted_file)
      os.environ['BORG_PASSPHRASE'] = config.get('borgbackup', 'passwd')
      os.environ['BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'] = "yes"
      os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = "yes"
      self.logger.info("Begin restore")
      print("Begin restore")
      rest_type = input("Please give the restore type wished, full or database: ")
      pitr = input("Give the point in time to restore to. (format: 2022-06-28 14:25:50): ")
      datum = pitr.split()
      starttime = str(datum[0])  + " 00:00:01"
      argname = self.server + "_borg_" + str(datum[0])
      borg = BorgBackup(self.config)
      code, out, err = borg.borgList(self.config.get('fs','borgdir'))
      res = out.decode("utf-8")
      res = res.split()
      pitr_dat = datetime.datetime.strptime(pitr, self.format)
      for item in res:
        if (item.find(argname)) != -1:
          flag = 1
          bckp_name = item
      if flag != 1:
        print("No corresponding Backup found for this PITR")
        self.logger.info("No corresponding Backup found for this PITR")
        os.remove(self.pidfile)
        exit(1)
      service = input("PLease give the service name of your MySQL database. (mysql.service, mysqld.service or mysql@instance.service): ")
      if rest_type == "full":
        if self.dbh != "False":
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
            os.remove(self.pidfile)
            exit(1)
        if snapshot.create_lvm_snapshot() == 0:
          self.logger.info("Mounting snapshot")
          if snapshot.mountsnap() == 0:
            rest_files,rest_path,dbname,starttimes = self.search_file(self.config,pitr,rest_type,self.config.get('misc','backuptype'))
            MySQL_Binlog = self.config.get('tools','mysqlbinlog') + " --no-defaults --start-datetime=\"" + starttime + "\" --stop-datetime=\"" + pitr + "\" "
            self.logger.info("Starting restore of the full MySQL server")
            print("Starting restore of the full MySQL server")
            cmd = "rm -rf " + self.config.get('mysql','dbdata') + "/*"
            os.system(cmd)
            if self.config.get('mysql','dblogs') != "":
              cmd = "rm -rf " + self.config.get('mysql','dblogs') + "/*"
              os.system(cmd)
            shutil.copy2(str(self.config.get('mycnf','log_error')),str(self.config.get('mycnf','log_error')+"_restore"))
            os.system("> " + str(self.config.get('mycnf','log_error')))
            code, out, err = borg.borgRestore(self.config.get('fs','borgdir'),bckp_name,"")
            res = out.decode("utf-8")
            res = res.split()
            cmd = self.config.get('tools','rsync') + " -a --delete " + self.config.get('fs','recover_dir') + self.config.get('fs','mountdir') + "/ " + self.config.get('mysql','dbdata') + "/"
            #self.logger(format(res))
            if err != 1:
              # code, out, err  = self.runCmd(cmd)
              os.system(cmd)
              self.logger.info("Unmounting snapshot")
              snapshot.umount(self.mountdir)
              self.logger.info("Destroying snapshot")
              snapshot.destroy_lvm_snapshot()
            else:
              print("The restore went wrong, you may want to roll back the snapshot")
              resp = input("Do you want to roll back the snapshot? (yes/no)")
              if resp == "yes":
                if snapshot.rollback(self.config.get('mysql','dbdata'),self.config.get('lvm','backuplv')) != 0:
                  self.logger.info("snapshot could not rolled back, you will have to umount " + self.config.get('mysql','dbdata') + " and remount it manually, then setart the mysql daemon")
                os.remove(self.pidfile)
                exit(1)
              else:
                self.logger.info("Umounting snapshot")
                snapshot.umount(self.mountdir)
                self.logger.info("Destroying snapshot")
                snapshot.destroy_lvm_snapshot()
                os.remove(self.pidfile)
                exit(1)
        shutil.copy2(str(self.config.get('mycnf','log_error')),str(self.config.get('mycnf','log_error')+"_restore"))
        os.system("> " + str(self.config.get('mycnf','log_error')))
        shutil.chown(self.config.get('mysql','dbdata'),"mysql","mysql")
        shutil.chown(self.config.get('mysql','dblogs'),"mysql","mysql")
        self.logger.info("Restarting MySQL server")
        print("Restarting MySQL server")
        cmd = "systemctl start " + service
        res = os.system(cmd)
        if res == 0:
          self.logger.info("MySQL server restarted")
          print("MySQL server restarted")
        else:
          self.logger.info("MySQL could not be started")
          resp = input("MySQL could not be started, please check the error log, correct any error and restart the serverc, once started, answer: yes")
          if resp != "yes":
            self.logger.info("MySQL could not be started, aborting")
            print("MySQL could not be started, please check the error log, correct any error and restart the restore. ")
            exit(1)
        for file in rest_files:
          MySQL_Binlog += file + " "
        MySQL_Binlog += "> binlogs"
        os.system(MySQL_Binlog)
        print("Starting recovery")
        self.logger.info("Starting recovery")
        cmd = "mysql -s -u" + self.conn_data["user"] + " -p" + self.conn_data["passwd"] + " < binlogs"
        os.system(cmd)
      elif rest_type == "database":
        self.logger.info("Trying to save the last logs if possible")
        print("Trying to save the last logs if possible")
        self.log_backup()
        if snapshot.create_lvm_snapshot() == 0:
          self.logger.info("Mounting snapshot")
          if snapshot.mountsnap() == 0:
            self.logger.info("Searching for the needed backup files")
            print("Searching for the needed backup files")
            rest_files,rest_path,dbname,starttimes = self.search_file(self.config,pitr,rest_type,self.config.get('misc','backuptype'))
            self.logger.info("Starting restore of database" + dbname)
            print("Starting restore of database " + dbname)
            code, out, err = borg.borgRestore(self.config.get('fs','borgdir'),bckp_name,rest_path)
            res = out.decode("utf-8")
            res = res.split()
            print(format(res))
            self.logger(format(res))
            self.logger.info("Stopping MySQL server")
            print("Stopping MySQL server")
            cmd = "systemctl stop " + service
            res = os.system(cmd)
            if res == 0:
              self.logger.info("MySQL is now stopped")
              print("MySQL is now stopped")
              if snapshot.rollback(self.config.get('mysql','dbdata'),self.config.get('lvm','backuplv')) == 0:
                cmd = "systemctl start " + service
                res = os.system(cmd)
              else:
                res = input("Please check if the snapshot has been rolled back, do it manually if not and restart mysql manually, once done answr with yes")
                if res != "yes":
                  exit(1)
        for file in rest_files:
          MySQL_Binlog = self.config.get('tools','mysqlbinlog') + " --no-defaults --database=" + dbname + " --start-datetime=\"" + starttimes[file] + "\" --stop-datetime=\"" + pitr + "\" "
          MySQL_Binlog += file + " "
        MySQL_Binlog += "> binlogs"
        os.system(MySQL_Binlog)
        print("Starting recovery")
        self.logger.info("Starting recovery")
        cmd = "mysql -s -u" + self.conn_data["user"] + " -p" + self.conn_data["passwd"] + " < binlogs"
        os.system(cmd)
      else:
        print("You probably misstype the restore type, please start over.")
    elif self.config.get('misc','backuptype') == "snapshot":
      pass
    elif self.config.get('misc','backuptype') == "tsm":
      pass
    elif self.config.get('misc','backuptype') == "hotStandby":
      pass
    else:
      print("It looks like you does not have any kind of backup yet!")
      self.logger.info("It looks like you does not have any kind of backup yet!")

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
    if self.args["bckptyp"] != "restore":
      self.dbh = mysql.connector.connect(**self.conn_data)
    else:
      self.dbh = "False"
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
    if self.args["bckptyp"] != "restore":
      self.logger.info("Starting Backup on server " + self.dbserver + ": " + str(self.datum))
    else:
      self.logger.info("Starting Restore on server " + self.dbserver + ": " + str(self.datum))
    self.pidfile = self.config.get('misc','mysql_backup_pid')
    self.mountdir = self.config.get('fs','mountdir')
    self.bckp = Bckp(self.backuptype,self.config,self.logger,self.conn_data,self.dbh,self.pidfile,**self.args)

  def run(self):
    if sys.version_info[0] < 3:
      logger.error("Python 3 or a more recent version is required.")
      raise Exception("Python 3 or a more recent version is required.")
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
      elif self.backuptype == 'borg':
        self.logger.info("Creating snapshot for borg backup")
        if snapshot.create_lvm_snapshot() == 0:
          self.logger.info("Mounting snapshot")
          if snapshot.mountsnap() == 0:
            self.bckp.borg()
          self.logger.info("Umounting snapshot")
          snapshot.umount(self.mountdir)
          self.logger.info("Destroying snapshot")
          snapshot.destroy_lvm_snapshot()
      elif self.backuptype == 'hotStandBy':
        self.logger.info("Creating snapshot for hotStandby")
        if snapshot.create_lvm_snapshot() == 0:
          self.logger.info("Mounting snapshot")
          if snapshot.mountsnap() == 0:
            self.bckp.hotStandby()
      else:
        self.bckp.mysqldump()
    elif self.args["bckptyp"] == "setup":
      pass
    else:
      self.bckp.restore()
    if self.args["bckptyp"] == "full":
      Cleaner(self.config,self.logger,self.backuptype)
    if self.dbh != "False":
      self.dbh.close()
    os.environ['BORG_PASSPHRASE'] = ""
    os.environ['BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'] = ""
    os.environ['BORG_RELOCATED_REPO_ACCESS_IS_OK'] = ""
    date = datetime.datetime.now()
    self.datum = date.strftime("%Y-%m-%d_%H-%M")
    self.logger.info("End of Backup on server " + self.dbserver + ": " + str(self.datum))
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
    self.config.set('fs','borgdir',basisbackupdir + "/borg")
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
  if sys.version_info[0] < 3:
    logger.error("Python 3 or a more recent version is required.")
    raise Exception("Python 3 or a more recent version is required.")
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


