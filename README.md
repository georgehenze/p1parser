p1parser
========

Logging of P1 messages to screen and database.

Usage:

python p1parser.py <options>

Available options: --quiet --mysql --daemon, --serialport, --daemon, --pidfile --config

--serialport, -p    : which serialport to use
--quiet, -q         : no output to console
--mysql, -m         : log parsed P1 messages to database, use together with --config
--daemon, -p        : fork script at startup, use in conjunction with --pidfile, no output to console
--pidfile           : location and name of the pidfile
--config            : specify path to config.xml file

Examples:

/python p1parser.py -p /dev/ttyUSB0 
 
/python p1parser.py --config /home/user/p1parser/config.xml --daemon


Example config.xml:

<config>
        <version>1</version>

        <serialport>/dev/ttyUSB0</serialport>

        <pid_create_file>yes</pid_create_file>
        <pid_file>/tmp/p1parser.pid</pid_file>

        <mysql_use>yes</mysql_use>
        <mysql_quit_on_error>yes</mysql_quit_on_error>

        <mysql_server>localhost</mysql_server>
        <mysql_database>database</mysql_database>
        <mysql_username>username</mysql_username>
        <mysql_password>password</mysql_password>
</config>

