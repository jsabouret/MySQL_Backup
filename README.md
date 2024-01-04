# MySQL Database backup program

(c) Joel Sabouret

## Table of contents
* [Introduction](#Introduction)
* [Prerequisites](#Prerequisites)
* [Setup](#Setup)

## Introduction

This program let you chose between different backup possibilities for your MySQL Database
It stores an encrypted MySQL DB connection string file, that can be used after the first run


### Possible value for backuptype
- 'nobackup    ==> Do nothing on the database just for testing purposes

- 'borg'      ==> synchronizes the datadir to another local directory

- 'mysqldump'  ==> Backup using standard mysqldump

- 'hotStandBy' ==> Synchronizes the Datadir with another MySQL server

- 'destsrv'     ==> distant server

- 'destsrvdir'  ==> Datadir on distant server

- 'destsrvproc' ==> MySQL service name on remote server e.G.(mysqld@instance, or mysqld)

1. Borg
 -- Is using borgbackup, the program is generating a snapshot of the database datadir and back it up with borgbackup.
2. mysqldump
 -- Uses the build in mysqldump, avoid using this when working on a high available server or a server with hosting data bigger than 20 GB
3. HotStandBy (Not implemented in the first version 0.0.1)
 -- Synchronize the database stand on a remote mysql server and start the DB. So you have a hot standby server with the stand of the last backup.



## Prerequisites

Before you begin this guide you'll need the following:

- Python>=3.9
- configparser >= 5.2
- argparse
- mysql_enc_ini >= 0.6
- cryptography >= 37.0
- borgbackup >= 1.2',
- mysql-connector-python >= 8.0 (installable from https://www.mysql.com)

## Setup

This program must be ran for the first time from the CLI,

```
python3 mysql_backup.py  -h
usage: connect to mysql tools [-h] [-H HOSTNAME] [-u USERNAME] [-d DATABASE] [-P PORT] [-D DEBUG] bckptyp

```

```
positional arguments:
  bckptyp               Full, logs or restore

optional arguments:
  -h, --help            show this help message and exit
  -H HOSTNAME, --host HOSTNAME
                        mysql server hostname.
  -u USERNAME, --user USERNAME
                        connect to mysql server user.
  -d DATABASE, --db DATABASE
                        Database name.
  -P PORT, --port PORT  Port number.
  -D DEBUG, --debug DEBUG
                        Debugging mode, check the program and don't do anything.   
  full|logs|restore
```
restore is only implemented in for MySQLdump backup type Version 0.0.1

You will be prompted for the password on the first call.

As well as the locations of :
- my.cnf
- Backups destination
- The backup type (when chosing borgbackup, this must be first installed (pip install -y borgbackup))

After this first initialization mysql_backup should be started from crontab. I recommend something like that

```
0 0 * * * bash -c 'source ~/.bash_profile; source ~/.bashrc;/usr/bin/python3 /root/bin/MySQL_Backup/mysql_backup.py -Hmysqlserver full' > /var/log/mysql/backup_mysql2_full.err 2>&1

*/30 1-23 * * * bash -c 'source ~/.bash_profile; source ~/.bashrc;/usr/bin/python3 /root/bin/MySQL_Backup/mysql_backup.py -Hmysqlserver logs' > /var/log/mysql/backup_mysql2_logs.err 2>&1
```