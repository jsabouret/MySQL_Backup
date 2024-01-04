#
# mysqlsnap configuration file
#
# Every line beginning with a pound sign (#) will be treated as a comment.
# Values should be put right after the equals sign, without whitespace.
# Please refer to the mysqlsnap(1) manual page for more information
#
# These values define how mysqlsnap should connect to the local MySQL server
# Usually host, port and socket path don't need to be provided, if the
# DBD::MySQL Perl module has been compiled with the same values that the local
# MySQL server uses. If a non-empty host name other than "localhost" is
# provided, the socket path is ignored.
#
# Please set all directory path with a last '/'   e.G. /var/log/mysql



#                [mysql]
# informations about database server



#           [lvm]
#  define volume groups and logical volume information
#


#        [fs]
# Filesystem options and directories destinations

#     [tools]
# Names of required external utilities
# Tools are scanned on the system during the first manual run
#
#


#      [misc]
# Other configuration options
#
# Possible value for backuptype
# 'nobackup'   ==> do nothing just for testing purposes
# 'tar'        ==> create a tar package
# 'rsync'      ==> synchronizes the datadir to another local directory
# 'borg'      ==> Use borg for Backup
# 'snap'       ==> Create only a snapshot
# 'tsm'        ==> backup the snapshot to TSM
# 'hotStandBy' ==> Synchronizes the Datadir with another MySQL server
#                       'destsrv'     ==> distant server
#                       'destsrvdir'  ==> Datadir on distant server
#                       'destsrvproc' ==> MySQL service name on remote server e.G.(mysqld@europe, or mysqld)
#
# for LZMA:
#compressarg=--stdout --verbose -7
# for bzip2:
#compressarg=--stdout --verbose -7
# for cat:
#compressarg=       # ie. nothing
#Anzahl der Backup
#

#    [logging]
# Logging options. The Sys::Syslog module is required for syslog option
# See "perldoc Sys::Syslog" for more information.
#
# 'console' (STDOUT, STDERR) or 'syslog' or 'both'.
# 'native', 'tcp', 'udp'. Default is 'native'
# If using remote syslog, don't forget to change the socket type to tcp or udp.

version='0.5'
release='0'
creation_date='2022-06-07'
build_date='2022-06-15'
configfiledir='/etc'
mountsfile='/proc/mounts'
cmds = (
'lvcreate',
'lvremove',
'lvs',
'vgdisplay',
'mount',
'tar',
'gzip',
'lzma',
'bzip2',
'rsync',
'borg',
'umount',
'dsmc',
'mysqldump',
'mysqlbinlog',
'mysqld'
)

default_conf ='''
[mysql]
dbserver =
dbuser =
dbdata =
dblogs =
mycnf =
mysqld_safe = /usr/sbin/mysqld
master =
log_bin_index =
log_basename =
database = mysql

[borg]
usage =
encryption = 
password_file = 
init = 

[lvm]
vgname =
lvname =
backuplv = mysql-backup
lvsize =
lvnmr = 100%%FREE

[fs]
xfs = 0
mountdir = /tmp/mysql_backup/mnt
recover_dir = /tmp/mysql_backup/restore
basisbackupdir =
backupdir =
backuplog =
backupusr =
borgdir =
relpath =

[tools]

[misc]
backuptype = mysqldump
backup2keep = 3
weekly_bckp = 2
configfiledir = /etc
configfile =
destsrv =
destsrvdir =
destsrvproc =
mysql_uid = 
mysql_gid =
optfile = /opt/tivoli/tsm/client/ba/bin/dsm_mysql.opt
mysql_backup_pid = /var/run/mysql_backup.pid
prefix = backup
suffix = _mysql
tararg = cvf
tarsuffixarg =
tarfilesuffix = .tar.gz
compressarg = --stdout --verbose --best
rsyncarg = -avWP --progress --human-readable --delete
borgarg = 7
datefmt = %%Y%%m%%d_%%H%%M%%S
innodb_recover = 1
pidfile = /tmp/mysqlsnap_recoverserver.pid
recover_socket = mysqlsnap.sock
skip_flush_tables = 0
extra_flush_tables = 0
skip_mycnf = 0
hooksdir = /usr/share/mysql_backup
skip_hooks = 0
keep_snapshot = 0
keep_mount = 0
quiet = 0

[logging]
logdir = /var/log/mysql
logfile = /var/log/mysql/backup_
log_method = console
syslog_socktype = native
syslog_facility =
syslog_remotehost =

[mycnf]
'''
backup_type = {
  'nobackup':'Don\'t do anything, just creating configfile and connection string',
  'mysqldump':'Backup with mysqldump rquires mysql-community-common',
  'tar': 'Backup with tar package & LVM2',
  'rsync': 'Backup with rsync package & LVM2',
  'borg': 'Backup with borg package & LVM2',
  'tsm': 'IBM Spectrum Protect (former TSM) & LVM2',
  'hotstandby': 'Backup on MySQL destination server & LVM2'
}
