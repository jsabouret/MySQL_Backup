#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import subprocess
#import datetime
#import logging
from subprocess import call
from mysql_enc_ini import Mysql_enc_ini

class BorgBackup:
  def __init__(self,config):
    #self.args = args
    self.config = config
    self.home = os.environ['HOME']
    #self.connect = Mysql_enc_ini(**self.args)
    my_list = str(self.config.get('mysql','dbserver')).split('.')
    self.server = my_list[0]
    self.borg = self.config.get('tools','borg')
    #self.pwdfile = self.home + "/" + self.server + "_" + str(self.config.get('mysql','database')) + "_" + str(self.config.get('mysql','dbuser')) + ".pwd"
    #self.conn_data = self.connect.decrypt(self.pwdfile)

  def borgcheck(self,repo):
    args = [self.borg,"check"]
    dirs = []
    excludes = []
    cmd = self.createCommand(args,repo,dirs,excludes)
    status = call(cmd)
    return status
    
  def borginit(self,repo):
    args = [self.borg,"init"]
    args.append("--encryption="+ str(self.config.get('borg','encryption')))
    dirs = []
    excludes = []
    cmd = self.createCommand(args,repo,dirs,excludes)
    if self.config.get('borg','encryption') != "none":
      print("Please insert the password for the encryption key:")
    status = call(cmd)
    return status

  def getkey(self,repo):
    args = [self.borg,"key","export"]
    dirs = []
    excludes = []
    cmd = self.createCommand(args,repo,dirs,excludes)
    status = call(cmd)
    return status

  def getDirs(self,backups,name):
    return backups[name]["dirs"]

  def getExcludes(self,backups,name):
    if( "excludes" in backups[name]):
      return backups[name]["excludes"]
    else:
      return list()

  def matchLabel(self,backups,name,label):
    if( "label" in backups[name]):
      plabel = backups[name]["label"]  ## label from backup list
      if(plabel == label):
        return True
      else:
        return False
    else:
      print("backup: " + name + " [error], label not set")
      return False
      
  def isAllDirsExists(self,dirs):
    allExists = True
    for dir in dirs:
      if(os.path.exists(dir) == False ):
        allExists = False
    return allExists

  def createCommand(self,args,repoArchive, dirs, excludes):
    for exclude in excludes:
      args.append("-e")
      args.append(exclude)
    args.append(repoArchive)
    for dir in dirs:
      args.append(dir)
    return args

  def borgBackup(self,repoArchive, name, dirs, excludes):
    args = [self.borg,"create","--stats"]
    repoArchive += "::" + name
    cmd = self.createCommand(args,repoArchive, dirs, excludes)
    code, out, err  = self.runCmd(cmd)
    return code, out, err 
    
  def borgCleaner(self,repoArchive, name, dirs, excludes):
    '''borg prune -v --list --keep-daily=7'''
    args = [self.borg,"prune","-v", "--list", "--keep-daily="+str(self.config.get('misc','backup2keep'))]
    repoArchive += "::" + name
    cmd = self.createCommand(args,repoArchive, dirs, excludes)
    status = call(cmd)
    return status
  
  def borgRestore(self,repoArchive,name,dbname):
    dirs = []
    excludes = []

    args = [self.borg,"extract"]
    repoArchive += "::" + name
    olddir = os.getcwd()
    if dbname == "":
      cmd = self.createCommand(args,repoArchive, dirs, excludes)
      os.chdir(self.config.get('fs','recover_dir'))
    else:
      dbdir = self.config.get('fs','mountdir')[1:] + "/" + dbname
      cmd = self.createCommand(args,repoArchive,dbdir)
      os.chdir(self.config.get('fs','recover_dir'))
    code, out, err  = self.runCmd(cmd)
    os.chdir(olddir)
    return code, out, err 
  
  def borgList(self,repoArchive):
    dirs = []
    excludes = []
    args = [self.borg,"list"]
    #repoArchive += "::" + name
    cmd = self.createCommand(args,repoArchive, dirs, excludes)
    code, out, err  = self.runCmd(cmd)
    return code, out, err 

  def runCmd(self,cmd):
    proc = subprocess.Popen(cmd,
    stdout = subprocess.PIPE,
    stderr = subprocess.PIPE,
    )
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout, stderr
## start


###  Commands 
# borg init --encryption=repokey-blake2 /path/to/repo
# borg create /path/to/repo::Monday ~/src ~/Documents
# borg create --stats /path/to/repo::Tuesday ~/src ~/Documents
# borg list /path/to/repo
# borg list /path/to/repo::Monday
# borg extract /path/to/repo::Monday
# borg delete /path/to/repo::Monday
# 




#1. Before a backup can be made a repository has to be initialized:
#
#             $ borg init --encryption=repokey /path/to/repo
#
#       2. Backup the ~/src and ~/Documents directories into an archive called Monday:
#
#             $ borg create /path/to/repo::Monday ~/src ~/Documents
#
#       3. The next day create a new archive called Tuesday:
#
#             $ borg create --stats /path/to/repo::Tuesday ~/src ~/Documents#
#
#          This backup will be a lot quicker and a lot smaller since only new never before seen  data  is  stored.  The
#          --stats option causes Borg to output statistics about the newly created archive such as the amount of unique
#          data (not shared with other archives):
#
#             ------------------------------------------------------------------------------
#             Archive name: Tuesday
#             Archive fingerprint: bd31004d58f51ea06ff735d2e5ac49376901b21d58035f8fb05dbf866566e3c2
#             Time (start): Tue, 2016-02-16 18:15:11
#             Time (end):   Tue, 2016-02-16 18:15:11
#
#             Duration: 0.19 seconds
#             Number of files: 127
#             ------------------------------------------------------------------------------
#                                   Original size      Compressed size    Deduplicated size
#             This archive:                4.16 MB              4.17 MB             26.78 kB
#             All archives:                8.33 MB              8.34 MB              4.19 MB
#
#                                   Unique chunks         Total chunks
#             Chunk index:                     132                  261
#             ------------------------------------------------------------------------------
#
#       4. List all archives in the repository:
#
#             $ borg list /path/to/repo
#             Monday                               Mon, 2016-02-15 19:14:44
#             Tuesday                              Tue, 2016-02-16 19:15:11
#
#       5. List the contents of the Monday archive:
#
#             $ borg list /path/to/repo::Monday
#             drwxr-xr-x user   group          0 Mon, 2016-02-15 18:22:30 home/user/Documents
#            -rw-r--r-- user   group       7961 Mon, 2016-02-15 18:22:30 home/user/Documents/Important.doc
#             ...
#
#       6. Restore the Monday archive by extracting the files relative to the current directory:
#
#             $ borg extract /path/to/repo::Monday
#
#       7. Recover disk space by manually deleting the Monday archive:
#
#             $ borg delete /path/to/repo::Monday
#
#       NOTE:
#          Borg is quiet by default (it works on WARNING log level).  You can use options like --progress or --list  to
#          get  specific  reports during command execution.  You can also add the -v (or --verbose or --info) option to
#          adjust the log level to INFO to get other informational messages.
#
#Positional Arguments and Options: Order matters
#       Borg only supports taking options (-s and --progress in the example) to the left or right of all positional ar-
#       guments (repo::archive and path in the example), but not in between them:#
#
#          borg create -s --progress repo::archive path  # good and preferred
#          borg create repo::archive path -s --progress  # also works
#          borg create -s repo::archive path --progress  # works, but ugly
#          borg create repo::archive -s --progress path  # BAD
