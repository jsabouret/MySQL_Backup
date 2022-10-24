# MySQL Database backup program

## Table of contents
* [Introduction](#Introduction)
* [Prerequisites](#Prerequisites)
* [Setup](#Setup)

## Introduction

This program let you chose between different backup possibilities for your MySQL Database
It stores an encrypted MySQL DB connection string file, that can be used after the first run


### Possible value for backuptype
> 'nobackup    ==> Do nothing on the database just for testing purposes
>
> 'borg'      ==> synchronizes the datadir to another local directory
>
> 'mysqldump'  ==> Backup using standard mysqldump
>
> 'hotStandBy' ==> Synchronizes the Datadir with another MySQL server
>
> - 'destsrv'     ==> distant server
>
> - 'destsrvdir'  ==> Datadir on distant server
>
> - 'destsrvproc' ==> MySQL service name on remote server e.G.(mysqld@instance, or mysqld)

1. Borg
 -- Is using borgbackup, the program is generating a snapshot of the database datadir and back it up with borgbackup.
2. mysqldump
 -- Uses the build in mysqldump, avoid using this when working on a high available server or a server with hosting data bigger than 20 GB
3. HotStandBy
 -- Synchronize the database stand on a remote mysql server and start the DB. So you have a hot standby server with the stand of the last backup.



## Prerequisites

Before you begin this guide you'll need the following:

- Python>=3.9
- configparser >= 5.2
- mysql.connector
- argparse
- mysql_enc_ini


## Setup

This program must be ran for the first time from the CLI,

```python3 mysql_backup.py  -h
usage: connect to mysql tools [-h] [-H HOSTNAME] [-u USERNAME] [-d DATABASE]
                              [-P PORT] [-D DEBUG(0-1)]
```

```optional arguments:
  -h, --help                    show this help message and exit
  -H HOSTNAME, --host HOSTNAME  mysql server hostname.  Default: localhost
  -u USERNAME, --user USERNAME  connect to mysql server user. Default: root
  -d DATABASE, --db DATABASE    Database name. Default: mysql
  -P PORT, --port PORT          Port number. Default: 3306
  -D DEBUG, --debug DEBUG       Debugging mode, check the program and don't do anything.         Default: 0
  full|logs
```

You will be prompted for the password on the first call.

As well as the locations of :
- my.cnf
- Backups destination
- The backup type

After this first initialization mysql_backup should be started from crontab. I recommend something like that

0 0 * * * bash -c 'source ~/.bash_profile; source ~/.bashrc;/usr/bin/python3 /root/bin/MySQL_Backup/mysql_backup.py -Hmysqlserver full' > /var/log/mysql/backup_mysql2_full.err 2>&1
*/30 1-23 * * * bash -c 'source ~/.bash_profile; source ~/.bashrc;/usr/bin/python3 /root/bin/MySQL_Backup/mysql_backup.py -Hmysqlserver logs' > /var/log/mysql/backup_mysql2_logs.err 2>&1



















This is _italics_, this is **bold**, and this is ~~strikethrough~~.

- This is a list item.
- This list is unordered.

1. This is a list item.
2. This list is ordered.

> This is a quote.
>
> > This is a quote inside a quote.
>
> - This is a list in a quote.
> - Another item in the quote list.

Here's how to include an image with alt text and a title:

![Alt text for screen readers](https://assets.digitalocean.com/logos/DO_Logo_horizontal_blue.png "DigitalOcean Logo")

Use horizontal rules to break up long sections:

---

Rich transformations are also applied:

- On ellipsis: ...
- On quote pairs: "sammy", 'test'
- On dangling single quotes: it's
- On en/em dashes: a -- b, a --- b

<!-- Comments will be removed from the output -->

| Tables | are   | also  | supported | and    | will   | overflow | cleanly | if     | needed |
|--------|-------|-------|-----------|--------|--------|----------|---------|--------|--------|
| col 1  | col 2 | col 3 | col 4     | col 5  | col 6  | col 7    | col 8   | col 9  | col 10 |
| col 1  | col 2 | col 3 | col 4     | col 5  | col 6  | col 7    | col 8   | col 9  | col 10 |
| col 1  | col 2 | col 3 | col 4     | col 5  | col 6  | col 7    | col 8   | col 9  | col 10 |
| col 1  | col 2 | col 3 | col 4     | col 5  | col 6  | col 7    | col 8   | col 9  | col 10 |
| col 1  | col 2 | col 3 | col 4     | col 5  | col 6  | col 7    | col 8   | col 9  | col 10 |


## Step 2 — Code

This is `inline code`. This is a <^>variable<^>. This is an `in-line code <^>variable<^>`.

Here's a configuration file with a label:

```nginx
[label /etc/nginx/sites-available/default]
server {
    listen 80 <^>default_server<^>;
    . . .
}
```

Examples can have line numbers, and every code block has a 'Copy' button to copy just the code:

```line_numbers,js
const test = 'hello';
const other = 'world';
console.log(test, other);
```

Here's output from a command with a secondary label:

```
[secondary_label Output]
Could not connect to Redis at 127.0.0.1:6379: Connection refused
```

This is a non-root user command example:

```command
sudo apt-get update
sudo apt-get install python3
```

This is a root command example:

```super_user
adduser sammy
shutdown
```

This is a custom prefix command example:

```custom_prefix(mysql>)
FLUSH PRIVILEGES;
SELECT * FROM articles;
```

A custom prefix can contain a space by using `\s`:

```custom_prefix((my-server)\smysql>)
FLUSH PRIVILEGES;
SELECT * FROM articles;
```

Indicate where commands are being run with environments:

```command
[environment local]
ssh root@server_ip
```

```command
[environment second]
echo "Secondary server"
```

```command
[environment third]
echo "Tertiary server"
```

```command
[environment fourth]
echo "Quaternary server"
```

```command
[environment fifth]
echo "Quinary server"
```

And all of these can be combined together, with a language for syntax highlighting as well as a line prefix (line numbers, command, custom prefix, etc.), and even an environment and label:

```line_numbers,html
[environment second]
[label index.html]
<html>
<body>
<head>
  <title><^>My Title<^></title>
</head>
<body>
  . . .
</body>
</html>
```


## Step 3 — Callouts

Here is a note, a warning, some info and a draft note:

<$>[note]
**Note:** Use this for notes on a publication.
<$>

<$>[warning]
**Warning:** Use this to warn users.
<$>

<$>[info]
**Info:** Use this for product information.
<$>

<$>[draft]
**Draft:** Use this for notes in a draft publication.
<$>

A callout can also be given a label, which supports inline markdown as well:

<$>[note]
[label Labels support _inline_ **markdown**]
**Note:** Use this for notes on a publication.
<$>


You can also mention users by username:

@MattIPv4


## Step 4 — Embeds

### YouTube

Embedding a YouTube video (id, height, width):

[youtube iom_nhYQIYk 225 400]

### DNS

Embedding DNS record lookups (hostname, record types...):

[dns digitalocean.com A AAAA]

### Glob

Demonstrating how glob matching works (pattern, tests...):

[glob **/*.js a/b.js c/d.js e.jsx f.md]

Glob embeds can also be written as multiple lines if needed:

[glob **/*.js
a/b.js
c/d.js
e.jsx
f.md]

### CodePen

Embedding a CodePen example (username, pen ID, flags...):

[codepen MattCowley vwPzeX]

Setting a custom height for the CodePen:

[codepen MattCowley vwPzeX 512]

Enabling dark mode on a CodePen embed:

[codepen MattCowley vwPzeX dark]

Setting the CodePen embed to only run when clicked:

[codepen MattCowley vwPzeX lazy]

Changing the default tab of a CodePen embed (can be html, css, or js):

[codepen MattCowley vwPzeX css]

Making the CodePen editable by the user (requires a Pro CodePen account):

[codepen chriscoyier Yxzjdz editable]

Combining different CodePen embed flags together is also supported:

[codepen MattCowley vwPzeX dark css 384]

### Glitch

Embedding a Glitch project (slug, flags...):

[glitch hello-digitalocean]

Setting a custom height for the Glitch project:

[glitch hello-digitalocean 512]

Showing the Glitch project code by default:

[glitch hello-digitalocean code]

Hiding the file tree by default when showing the Glitch project code:

[glitch hello-digitalocean code notree]

Setting a default file to show, and highlighting lines in the file:

[glitch hello-digitalocean code path=src/app.jsx highlights=15,25]

Removing the author attribution from the Glitch embed:

[glitch hello-digitalocean noattr]

### Can I Use

Embedding usage information from Can I Use (feature slug, flags...):

[caniuse css-grid]

Control how many previous browser versions are listed (0-5):

[caniuse css-grid past=5]

Control how many future browser versions are listed (0-3):

[caniuse css-grid future=3]

Enable the accessible color scheme by default:

[caniuse css-grid accessible]

### Asciinema

Embedding a terminal recording from Asciinema:

[asciinema 239367]

Setting a custom number of cols and rows for the Asciinema terminal:

[asciinema 239367 50 20]


## Step 5 — Tutorials

Certain features of our Markdown engine are designed specifically for our tutorial content-types.
These may not be enabled in all contexts in the DigitalOcean community, but are enabled by default in the do-markdownit plugin.

[rsvp_button 1234 "Marketo RSVP buttons use the `rsvp_button` flag"]

[terminal ubuntu:focal Terminal buttons are behind the `terminal` flag]


## Conclusion

Please refer to our [writing guidelines](https://do.co/style) for more detailed explanations on our style and formatting.