#!/usr/bin/python
# coding=UTF-8

# ----------------------------------------------------------------------------
#   
#   p1parser.py
#   
#   Copyright (C) 2012 George Henze
#   
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#   Portions of the parsing code were written by http://www.smartmeterdashboard.nl/
#   under Creative Commons license. 
#
# ----------------------------------------------------------------------------

import sys
import serial
import locale
import datetime
import signal
import getopt
import os

from xml.dom.minidom import parseString
import xml.dom.minidom as minidom

class config_data:
    def __init__(
        self, 
        mysql_server = "",
        mysql_database = "",
        mysql_username = "",
        mysql_password = "",
        port = "",
        create_pid = False,
        pidfile = "",
        daemon = False,
        configfile = "",
        consolelogging = True,
        databaselogging = False,
        database_quit_on_error = True):
        
        self.mysql_server = mysql_server
        self.mysql_database = mysql_database
        self.mysql_username = mysql_username
        self.mysql_password = mysql_password
        self.port = port
        self.create_pid = create_pid
        self.pidfile = pidfile
        self.daemon = daemon
        self.databaselogging = databaselogging
        self.database_quit_on_error = database_quit_on_error
        self.configfile = configfile
        self.consolelogging = consolelogging

configdata = config_data()

sw_name = "P1 Parser"
sw_version = "0.1a"

print "Starting "+ sw_name + ' ' + sw_version

# Check Python version
if sys.version_info < (2, 5):
    print "Sorry, requires Python 2.5, 2.6 or 2.7."
    sys.exit(1)

# Shutdown
def shutdown():
    # clean up PID file after us
    if configdata.create_pid:
        print("Removing pidfile " + str(configdata.pidfile))
        os.remove(configdata.pidfile)
    
    # close serial port
    try:
        ser.close()
    except:
        sys.exit ("Can't close serial port %s." % ser.name )
    
    os._exit(0)
    
# Signal handler
def handler(signum=None, frame=None):
    if type(signum) != type(None):
        print("Signal %i caught, exiting..." % int(signum))
        shutdown()

signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

def daemonize():
    try:
        pid = os.fork()
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))

    os.setsid() 

    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    try:
        pid = os.fork() 
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if configdata.create_pid:
        pid = str(os.getpid())
        print("Writing PID " + pid + " to " + str(configdata.pidfile))
        file(configdata.pidfile, 'w').write("%s\n" % pid)

def read_config(configFile,configItem):
 
        #open the xml file for reading:
        file = open(configFile,'r')
        data = file.read()
        file.close()
        dom = parseString(data)
        
        # Get config item
        xmlTag = dom.getElementsByTagName( configItem )[0].toxml()
        xmlData=xmlTag.replace('<' + configItem + '>','').replace('</' + configItem + '>','')
        return xmlData

def load_config_file(configfile):
    if os.path.exists(configfile):  
        configdata.port = read_config(configfile, "serialport")
        
        if (read_config(configfile, "pid_create_file") == "yes"):
            configdata.create_pid = True
        else:
            configdata.create_pid = False
        
        configdata.pidfile = read_config(configfile, "pid_file")
        
        # read mysql configuration
        if (read_config(configfile, "mysql_use") == "yes"):
            configdata.databaselogging = True
        else:
            configdata.databaselogging = False

        if (read_config(configfile, "mysql_quit_on_error") == "yes"):
            configdata.database_quit_on_error = True
        else:
            configdata.database_quit_on_error = False

        configdata.mysql_server = read_config(configfile, "mysql_server")
        configdata.mysql_database = read_config(configfile, "mysql_database")
        configdata.mysql_username = read_config(configfile, "mysql_username")
        configdata.mysql_password = read_config(configfile, "mysql_password")
    else:
        # config file not found, set default values
        print "Error: Configuration file not found (" + configfile + ")"
        

def log_database():
    try:
        db = MySQLdb.connect(configdata.mysql_server, configdata.mysql_username, configdata.mysql_password, configdata.mysql_database)
        cursor = db.cursor()

        query = "insert into p1_log values (\'" + \
                 P1.timestamp + "\',\'" + \
                 P1.meter_supplier + "\',\'" + \
                 P1.header + "\',\'" + \
                 P1.dsmr_version + "\',\'" + \
                 P1.equipment_id + "\',\'" + \
                 str(P1.meterreading_in_1) + "\',\'" + \
                 P1.unitmeterreading_in_1 + "\',\'" + \
                 str(P1.meterreading_in_2) + "\',\'" + \
                 P1.unitmeterreading_in_2 + "\',\'" + \
                 str(P1.meterreading_out_1) + "\',\'" +\
                 P1.unitmeterreading_out_1 + "\',\'" + \
                 str(P1.meterreading_out_2) + "\',\'" + \
                 P1.unitmeterreading_out_2 + "\',\'" + \
                 str(P1.current_tariff) + "\',\'" + \
                 str(P1.current_power_in) + "\',\'" + \
                 P1.unit_current_power_in + "\',\'" + \
                 str(P1.current_power_out) + "\',\'" + \
                 P1.unit_current_power_out + "\',\'" + \
                 str(P1.current_threshold) + "\',\'" + \
                 P1.unit_current_threshold + "\',\'" + \
                 P1.current_switch_position + "\',\'" + \
                 str(P1.powerfailures) + "\',\'" + \
                 str(P1.long_powerfailures) + "\',\'" + \
                 P1.long_powerfailures_log + "\',\'" + \
                 str(P1.voltage_sags_l1)  + "\',\'" + \
                 str(P1.voltage_sags_l2) + "\',\'" + \
                 str(P1.voltage_sags_l3) + "\',\'" + \
                 str(P1.voltage_swells_l1) + "\',\'" + \
                 str(P1.voltage_swells_l2) + "\',\'" + \
                 str(P1.voltage_swells_l3) + "\',\'" + \
                 P1.message_code + "\',\'" + \
                 P1.message_text + "\',\'" + \
                 str(P1_channel_1.id) + "\',\'" + \
                 str(P1_channel_1.type_id) + "\',\'" +  \
                 P1_channel_1.type_desc + "\',\'" + \
                 str(P1_channel_1.equipment_id) + "\',\'" + \
                 P1_channel_1.timestamp + "\',\'" + \
                 str(P1_channel_1.meterreading) + "\',\'" + \
                 P1_channel_1.unit + "\',\'" + \
                 str(P1_channel_1.valveposition) + "\',\'" + \
                 str(P1_channel_2.id) + "\',\'" + \
                 str(P1_channel_2.type_id) + "\',\'" +  \
                 P1_channel_2.type_desc + "\',\'" + \
                 str(P1_channel_2.equipment_id) + "\',\'" + \
                 P1_channel_2.timestamp + "\',\'" + \
                 str(P1_channel_2.meterreading) + "\',\'" + \
                 P1_channel_2.unit + "\',\'" + \
                 str(P1_channel_2.valveposition) + "\',\'" + \
                 str(P1_channel_3.id) + "\',\'" + \
                 str(P1_channel_3.type_id) + "\',\'" + \
                 P1_channel_3.type_desc + "\',\'" + \
                 str(P1_channel_3.equipment_id) + "\',\'" + \
                 P1_channel_3.timestamp + "\',\'" + \
                 str(P1_channel_3.meterreading) + "\',\'" + \
                 P1_channel_3.unit + "\',\'" + \
                 str(P1_channel_3.valveposition) + "\',\'" + \
                 str(P1_channel_4.id) + "\',\'" + \
                 str(P1_channel_4.type_id) + "\',\'" + \
                 P1_channel_4.type_desc + "\',\'" + \
                 str(P1_channel_4.equipment_id) + "\',\'" + \
                 P1_channel_4.timestamp + "\',\'" + \
                 str(P1_channel_4.meterreading) + "\',\'" + \
                 P1_channel_4.unit + "\',\'" + \
                 str(P1_channel_4.valveposition)  + "\')"
        cursor.execute(query)
        db.commit()
    
        if configdata.consolelogging:
            print("Record inserted into database.")
            
    except MySQLdb.Error, e:
        print "Database error %d: %s" % (e.args[0], e.args[1])
        if configdata.database_quit_on_error:
            sys.exit(1)

def log_console():
    print ("---------------------------------------------------------------------------------------")
    print ("P1 telegram ontvangen op: %s" % P1.timestamp)
    if P1.meter_supplier == "KMP":
        print ("Fabrikant: Kamstrup")
    elif P1.meter_supplier == "ISk":
        print ("Fabrikant: IskraEmeco")
    elif P1.meter_supplier == "XMX":
        print ("Fabrikant: Xemex")
    else:
        print ("Meter fabrikant: Niet herkend")
        
    print ("Meter informatie: %s" % P1.header )
    print (" 0. 2. 8 - DSMR versie: %s" % P1.dsmr_version )
    print ("96. 1. 1 - Meternummer Elektriciteit: %s" % P1.equipment_id )
    print (" 1. 8. 1 - Meterstand Elektriciteit levering (T1/Laagtarief): %0.3f %s" % (P1.meterreading_in_1,P1.unitmeterreading_in_1) )
    print (" 1. 8. 2 - Meterstand Elektriciteit levering (T2/Normaaltarief): %0.3f %s" % (P1.meterreading_in_2,P1.unitmeterreading_in_2) )
    print (" 2. 8. 1 - Meterstand Elektriciteit teruglevering (T1/Laagtarief): %0.3f %s" % (P1.meterreading_out_1,P1.unitmeterreading_out_1) )
    print (" 2. 8. 2 - Meterstand Elektriciteit teruglevering (T2/Normaaltarief): %0.3f %s" % (P1.meterreading_out_2,P1.unitmeterreading_out_2) )
    print ("96.14. 0 - Actueel tarief Elektriciteit: %d" % P1.current_tariff )
    print (" 1. 7. 0 - Actueel vermogen Electriciteit levering (+P): %0.3f %s" % (P1.current_power_in,P1.unit_current_power_in) )
    print (" 2. 7. 0 - Actueel vermogen Electriciteit teruglevering (-P): %0.3f %s" % (P1.current_power_out,P1.unit_current_power_out) )
    print ("17. 0. 0 - Actuele doorlaatwaarde Elektriciteit: %0.3f %s" % (P1.current_threshold,P1.unit_current_threshold) )
    print ("96. 3.10 - Actuele schakelaarpositie Elektriciteit: %s" % P1.current_switch_position )
    print ("96. 7.21 - Aantal onderbrekingen Elektriciteit: %s" % P1.powerfailures )
    print ("96. 7. 9 - Aantal lange onderbrekingen Elektriciteit: %s" % P1.long_powerfailures )
    print ("99.97. 0 - Lange onderbrekingen Elektriciteit logboek: %s" % P1.long_powerfailures_log )
    print ("32.32. 0 - Aantal korte spanningsdalingen Elektriciteit in fase 1: %s" % P1.voltage_sags_l1 )
    print ("52.32. 0 - Aantal korte spanningsdalingen Elektriciteit in fase 2: %s" % P1.voltage_sags_l2 )
    print ("72.32. 0 - Aantal korte spanningsdalingen Elektriciteit in fase 3: %s" % P1.voltage_sags_l3 )
    print ("32.36. 0 - Aantal korte spanningsstijgingen Elektriciteit in fase 1: %s" % P1.voltage_swells_l1 )
    print ("52.36. 0 - Aantal korte spanningsstijgingen Elektriciteit in fase 2: %s" % P1.voltage_swells_l2 )
    print ("72.36. 0 - Aantal korte spanningsstijgingen Elektriciteit in fase 3: %s" % P1.voltage_swells_l3 )       
    print ("96.13. 1 - Bericht code: %s" % P1.message_code )
    print ("96.13. 0 - Bericht tekst: %s" % P1.message_text )
    
    channellist = []        
    channellist = [P1_channel_1, P1_channel_2, P1_channel_3, P1_channel_4]
    for channel in channellist:
        if channel.id != 0:
            print ("MBus Meterkanaal: %s" % channel.id )
            print ("24. 1. 0 - Productsoort: %s (%s)" % (channel.type_id, channel.type_desc) )
            print ("91. 1. 0 - Meternummer %s: %s" % (channel.type_desc, channel.equipment_id) )
            if P1.dsmr_version != "40":
                print ("24. 3. 0 - Tijdstip meterstand %s levering: %s" % (channel.type_desc, channel.timestamp) )
                print ("24. 3. 0 - Meterstand %s levering: %0.3f %s" % (channel.type_desc, channel.meterreading, channel.unit) )
            else:
                print ("24. 2. 1 - Tijdstip meterstand %s levering: %s" % (channel.type_desc, channel.timestamp) )
                print ("24. 2. 1 - Meterstand %s levering: %0.3f %s" % (channel.type_desc, channel.meterreading, channel.unit) )            
            print ("24. 4. 0 - Actuele kleppositie %s: %s" % (channel.type_desc,channel.valveposition) )
    print ("Einde P1 telegram" )
    return  

class P1_Data:
    def __init__(
        self,
        timestamp='0000-00-00 00:00:00',
        meter_supplier="",
        header="",
        dsmr_version="30",
        equipment_id=0,
        meterreading_in_1=0,
        unitmeterreading_in_1="",
        meterreading_in_2=0,
        unitmeterreading_in_2="",
        meterreading_out_1=0,
        unitmeterreading_out_1="",
        meterreading_out_2=0,
        unitmeterreading_out_2="",
        current_tariff=0,
        current_power_in=0,
        current_power_out=0,
        current_threshold=0,
        current_switch_position=0,
        unit_current_threshold="",
        powerfailures=0,
        long_powerfailures=0,
        long_powerfailures_log="",
        voltage_sags_l1=0,
        voltage_sags_l2=0,
        voltage_sags_l3=0,
        voltage_swells_l1=0,
        voltage_swells_l2=0,
        voltage_swells_l3=0,
        message_code="",
        message_text=""):
        
        self.timestamp = timestamp
        self.meter_supplier = meter_supplier
        self.header = header
        self.dsmr_version = dsmr_version
        self.equipment_id = equipment_id
        self.meterreading_in_1 = meterreading_in_1,
        self.unitmeterreading_in_1 = unitmeterreading_in_1,
        self.meterreading_in_2 = meterreading_in_2,
        self.unitmeterreading_in_2 = "",
        self.meterreading_out_1 = meterreading_out_1,
        self.unitmeterreading_out_1 = unitmeterreading_out_1,
        self.meterreading_out_2 = meterreading_out_2,
        self.unitmeterreading_out_2 = unitmeterreading_out_2,
        self.current_tariff = current_tariff,
        self.current_power_in = current_power_in,
        self.current_power_out = current_power_out,
        self.current_threshold = current_threshold,
        self.current_switch_position = current_switch_position,
        self.unit_current_threshold = unit_current_threshold,
        self.powerfailures = powerfailures
        self.long_powerfailures = long_powerfailures
        self.long_powerfailures_log = long_powerfailures_log
        self.voltage_sags_l1 = voltage_sags_l1
        self.voltage_sags_l2 = voltage_sags_l2
        self.voltage_sags_l3 = voltage_sags_l3
        self.voltage_swells_l1 = voltage_swells_l1
        self.voltage_swells_l2 = voltage_swells_l2
        self.voltage_swells_l3 = voltage_swells_l3
        self.message_code = message_code
        self.message_text = message_text

class P1_ChannelData:
    def __init__(
        self, 
        id=0, 
        type_id=0, 
        type_desc='', 
        equipment_id='', 
        timestamp='0000-00-00 00:00:00', 
        meterreading=0.0, 
        unit='', 
        valveposition=0):
        
        self.id = id
        self.type_id = type_id
        self.type_desc = type_desc
        self.equipment_id = equipment_id
        self.timestamp = timestamp
        self.meterreading = meterreading
        self.unit = unit
        self.valveposition = valveposition

# MAIN
try:
    opts, args = getopt.getopt(sys.argv[1:], "qmdp::", ['quiet', 'mysql', 'daemon', 'serialport=', 'pidfile=', 'config='])  

except getopt.GetoptError:
    print "Available Options: --quiet --mysql --daemon, --serialport, --daemon, --pidfile --config"
    sys.exit()

for o, a in opts:
    if o in ('-q', '--quiet'):
        configdata.consolelogging = False

    if o in ('-p', '--serialport'):
        configdata.port = a
        if configdata.consolelogging:
            print("Reading port " + configdata.port)

    if o in ('-m', '--mysql'):
        configdata.databaselogging = True
        
        if configdata.consolelogging:
            print("Logging to server: " + configdata.mysql_server + ", database: " + configdata.mysql_database)
        
    if o in ('--pidfile'):
        configdata.pidfile = os.path.abspath(a)
        configdata.create_pid = True
        if configdata.consolelogging:
            print("Using PID file " + configdata.pidfile)
    
    if o in ('-d', '--daemon'):
        configdata.daemon = True
        configdata.consolelogging = False
        
    if o in ('--config'):
        configdata.configfile = os.path.abspath(a)
        if configdata.consolelogging:
            print("Using config file " + configdata.configfile)
        
        load_config_file(configdata.configfile)

if configdata.create_pid == False and configdata.daemon:
    print("Use --pidfile when starting as daemon. Exiting.")
    sys.exit(1)

       
if configdata.create_pid:
    if os.path.exists(configdata.pidfile):
        sys.exit("PID file '" + configdata.pidfile + "' already exists. Exiting.")
    try:
        file(configdata.pidfile, 'w').write("pid\n")
    except IOError, e:
        raise SystemExit("Unable to write PID file: %s [%d]" % (e.strerror, e.errno))

if (configdata.consolelogging == False) and (configdata.databaselogging == False):
    print "Error: you can't run the script if either one of options --quiet or --database is not set."
    sys.exit(1)

if configdata.databaselogging:
    # import MySQLdb
    try:
        import MySQLdb
    except ImportError:
        print "Error: You need to install MySQL extension for Python"
        sys.exit(1)

if configdata.consolelogging:
    print "Start decoding messages"
    
if configdata.daemon:
    daemonize()

# init serial port
ser = serial.Serial()
ser.baudrate = 9600
ser.bytesize=serial.SEVENBITS
ser.parity=serial.PARITY_EVEN
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port=configdata.port
          
# check serial port
try:
    ser.open()
except:
    sys.exit ("Failed to connect to port %s, exiting."  % ser.name)

# init new telegram
P1_teller=0
P1=P1_Data()    
P1_Telegram=False

# run until signal
while 1:
    P1_line=''

    try:
        P1_raw = ser.readline()
    except:
        sys.exit ("Can't read serial port %s." % ser.name )
        ser.close
 
    P1_str=str(P1_raw)
    P1_line=P1_str.strip()

    # telegram starts with /
    if P1_line[0:1] == "/":
        P1_teller = P1_teller +1        
        P1_Telegram=True
        
        P1.timestamp=datetime.datetime.strftime(datetime.datetime.today(), "%Y-%m-%d %H:%M:%S" )
        
        # init new P1 Channel objects
        P1_channel_1=P1_ChannelData()
        P1_channel_2=P1_ChannelData()
        P1_channel_3=P1_ChannelData()
        P1_channel_4=P1_ChannelData()
        
        P1.meter_supplier=P1_line[1:4]
        P1.header=P1_line
    
    elif P1_line[4:9] == "1.0.0":
        #P1 Timestamp (DSMR 4)
        #eg. 0-0:1.0.0(101209113020W)
        P1.timestamp="20"+P1_line[10:12]+"-"+P1_line[12:14]+"-"+P1_line[14:16]+" "+P1_line[16:18]+":"+P1_line[18:20]+":"+P1_line[20:22]

    elif P1_line[4:9] == "0.2.8":
        #DSMR Version (DSMR V4)
        #eg. 1-3:0.2.8(40)
        P1_lastpos=len(P1_line)-1
        P1.dsmr_version=P1_line[10:P1_lastpos]
      
    elif P1_line[4:10] == "96.1.1":
        #Equipment identifier (Electricity)
        #eg. 0-0:96.1.1(204B413655303031353131323039393130)
        P1_lastpos=len(P1_line)-1
        P1.equipment_id=P1_line[11:P1_lastpos]

    elif P1_line[4:9] == "1.8.1":
        #Meter Reading electricity delivered to client (normal tariff)
        #eg. 1-0:1.8.1(00721.000*kWh) (DSMR 3)
        #eg. 1-0:1.8.1(000038.851*kWh) (DSMR 4)
        #        P1_meterreading_in_1=float(P1_line[10:19])
        #        P1_unitmeterreading_in_1=P1_line[20:23]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.meterreading_in_1=float(P1_line[P1_num_start:P1_num_end])        
        P1.unitmeterreading_in_1=P1_line[P1_num_end+1:P1_lastpos]
        
    elif P1_line[4:9] == "1.8.2":
        #Meter Reading electricity delivered to client (low tariff)
        #eg. 1-0:1.8.2(00392.000*kWh)
        #        P1_meterreading_in_2=float(P1_line[10:19])
        #        P1_unitmeterreading_in_2=P1_line[20:23]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.meterreading_in_2=float(P1_line[P1_num_start:P1_num_end])        
        P1.unitmeterreading_in_2=P1_line[P1_num_end+1:P1_lastpos]

    elif P1_line[4:9] == "2.8.1":
        #Meter Reading electricity delivered by client (normal tariff)
        #eg. 1-0:2.8.1(00000.000*kWh)
        #        P1_meterreading_out_1=float(P1_line[10:19])
        #        P1_unitmeterreading_out_1=P1_line[20:23]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.meterreading_out_1=float(P1_line[P1_num_start:P1_num_end])        
        P1.unitmeterreading_out_1=P1_line[P1_num_end+1:P1_lastpos]

    elif P1_line[4:9] == "2.8.2":
        #Meter Reading electricity delivered by client (low tariff)
        #eg. 1-0:2.8.2(00000.000*kWh)
        #        P1_meterreading_out_2=float(P1_line[10:19])
        #        P1_unitmeterreading_out_2=P1_line[20:23]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.meterreading_out_2=float(P1_line[P1_num_start:P1_num_end])        
        P1.unitmeterreading_out_2=P1_line[P1_num_end+1:P1_lastpos]

    elif P1_line[4:11] == "96.14.0":
        #Tariff indicator electricity
        #eg. 0-0:96.14.0(0001)
        #alternative 0-0:96.14.0(1)
        P1_lastpos=len(P1_line)-1
        P1.current_tariff=float(P1_line[12:P1_lastpos])

    elif P1_line[4:9] == "1.7.0":
        #Actual electricity power delivered to client (+P)
        #eg. 1-0:1.7.0(0000.91*kW)
        #        P1_current_power_in=float(P1_line[10:17])
        #        P1_unit_current_power_in=P1_line[18:20]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.current_power_in=float(P1_line[P1_num_start:P1_num_end])        
        P1.unit_current_power_in=P1_line[P1_num_end+1:P1_lastpos]

    elif P1_line[4:9] == "2.7.0":
        #Actual electricity power delivered by client (-P)
        #1-0:2.7.0(0000.00*kW)
        #        P1_current_power_out=float(P1_line[10:17])
        #        P1_unit_current_power_out=P1_line[18:20]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.current_power_out=float(P1_line[P1_num_start:P1_num_end])        
        P1.unit_current_power_out=P1_line[P1_num_end+1:P1_lastpos]

    elif P1_line[4:10] == "17.0.0":
        #Actual threshold Electricity
        #Companion standard, eg Kamstrup, Xemex
        #eg. 0-0:17.0.0(999*A)
        #Iskraemeco
        #eg. 0-0:17.0.0(0999.00*kW)
        #Companion Standard        
        #        P1_current_threshold=float(P1_line[11:14])
        #        P1_unit_current_threshold=P1_line[15:16]
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1.current_threshold=float(P1_line[P1_num_start:P1_num_end])        
        P1.unit_current_threshold=P1_line[P1_num_end+1:P1_lastpos]
                
    elif P1_line[4:11] == "96.3.10":
        #Actual switch position Electricity (in/out/enabled).
        #eg. 0-0:96.3.10(1)
        P1.current_switch_position=P1_line[12:13]

    elif P1_line[4:11] == "96.7.21":
        #Number of powerfailures in any phase (DSMR v4)
        #eg. 0-0:96.7.21(00004)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.powerfailures=int(float(P1_line[P1_num_start:P1_lastpos]))
    
    elif P1_line[4:10] == "96.7.9":
        #Number of long powerfailures in any phase (DSMR v4)
        #eg. 0-0:96.7.9(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.long_powerfailures=int(float(P1_line[P1_num_start:P1_lastpos]))
    
    elif P1_line[4:11] == "99:97.0":
        #Powerfailure eventlog
        #eg. 1-0:99:97.0(2)(0:96.7.19)(101208152415W)(0000000240*s)(101208151004W)(00000000301*s)
        P1_lastpos=len(P1_line)
        P1_log_start= P1_line.find("0:96.7.19") +10
        P1.long_powerfailures_log=P1_line[P1_log_start:P1_lastpos]
    
    elif P1_line[4:11] == "32.32.0":
        #Number of Voltage sags L1
        #eg. 1-0:32.32.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_sags_l1=int(float(P1_line[P1_num_start:P1_lastpos]))

    elif P1_line[4:11] == "52.32.0":
        #Number of Voltage sags L2
        #eg. 1-0:52.32.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_sags_l2=int(float(P1_line[P1_num_start:P1_lastpos]))

    elif P1_line[4:11] == "72.32.0":
        #Number of Voltage sags L3
        #eg. 1-0:72.32.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_sags_l3=int(float(P1_line[P1_num_start:P1_lastpos]))
    
    elif P1_line[4:11] == "32.36.0":
        #Number of Voltage swells L1
        #eg. 1-0:32.36.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_swells_l1=int(float(P1_line[P1_num_start:P1_lastpos]))

    elif P1_line[4:11] == "52.36.0":
        #Number of Voltage swells L2
        #eg. 1-0:52.36.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_swells_l2=int(float(P1_line[P1_num_start:P1_lastpos]))

    elif P1_line[4:11] == "72.36.0":
        #Number of Voltage swells L3
        #eg. 1-0:72.36.0(00002)
        P1_lastpos=len(P1_line)-1
        P1_num_start = P1_line.find("(") +1
        P1.voltage_swells_l3=int(float(P1_line[P1_num_start:P1_lastpos]))

    
    elif P1_line[4:11] == "96.13.1":
        #Text message code: numeric 8 digits
        #eg. 0-0:96.13.1()
        P1_lastpos=len(P1_line)-1
        #P1_message_code=P1_line[12:P1_lastpos]
        P1.message_code=P1_line[12:P1_lastpos]
#        bytes.fromhex(P1_line[12:P1_lastpos]).decode('-8')

    elif P1_line[4:11] == "96.13.0":
        #Text message max 1024 characters.
        #eg. 0-0:96.13.0()
        P1_lastpos=len(P1_line)-1
        P1.message_text=P1_line[12:P1_lastpos]
        #P1_line[12:P1_lastpos]

    #####
    #Channels 1/2/3/4: MBus connected meters
    #####
    elif P1_line[4:10] == "24.1.0":
        #Device-Type
        #eg. 0-1:24.1.0(3)
        #or 0-1:24.1.0(03) 3=Gas;5=Heat;6=Cooling
        P1_channel=int(P1_line[2:3])
        P1_lastpos=len(P1_line)-1
        P1_value=int(P1_line[11:P1_lastpos])
        if P1_value in [3,7]:
           P1_value2="Gas"
        elif P1_value == 5:
             P1_value2="Warmte"
        elif P1_value == 6:
             P1_value2="Koude"
        elif P1_value == 8:
             P1_value2="Koud tapwater"
        elif P1_value == 9:
             P1_value2="Warm tapwater"
        else:
             P1_value2="Onbekend"

        if P1_Telegram:
            # self, id=None, type_id=None, type_desc=None, equipment_id=None, timestamp=None, meterreading=None, unit=None, valveposition=None
            if P1_channel==1:
                P1_channel_1.id=P1_channel
                P1_channel_1.type_id=P1_value
                P1_channel_1.type_desc=P1_value2
            elif P1_channel==2:
                P1_channel_2.id=P1_channel
                P1_channel_2.type_id=P1_value
                P1_channel_2.type_desc=P1_value2
            elif P1_channel==3:
                P1_channel_3.id=P1_channel
                P1_channel_3.type_id=P1_value
                P1_channel_3.type_desc=P1_value2
            elif P1_channel==4:
                P1_channel_4.id=P1_channel
                P1_channel_4.type_id=P1_value
                P1_channel_4.type_desc=P1_value2
            

    elif P1_line[4:10] == "96.1.0" and P1_Telegram:
        #Equipment identifier
        #eg. 0-1:96.1.0(3238303039303031303434303132303130)
        P1_channel=int(P1_line[2:3])
        P1_lastpos=len(P1_line)-1
        P1_value=P1_line[11:P1_lastpos]

        #self, id=None, type_id=None, type_desc=None, equipment_id=None, timestamp=None, meterreading=None, unit=None, valveposition=None
        if P1_channel==1:
            P1_channel_1.equipment_id=P1_value
        elif P1_channel==2:
            P1_channel_2.equipment_id=P1_value
        elif P1_channel==3:
            P1_channel_3.equipment_id=P1_value
        elif P1_channel==4:
            P1_channel_4.equipment_id=P1_value

    elif P1_line[4:10] == "24.3.0" and P1_Telegram:
        #Last hourly value delivered to client (DSMR < V4)
        #eg. Kamstrup/Iskraemeco:
        #0-1:24.3.0(110403140000)(000008)(60)(1)(0-1:24.2.1)(m3)
        #(00437.631)
        #eg. Companion Standard:
        #0-1:24.3.0(110403140000)(000008)(60)(1)(0-1:24.2.1)(m3)(00437.631)
        P1_channel=int(P1_line[2:3])
        P1_channel_timestamp="20"+P1_line[11:13]+"-"+P1_line[13:15]+"-"+P1_line[15:17]+" "+P1_line[17:19]+":"+P1_line[19:21]+":"+P1_line[21:23]
        P1_lastpos=len(P1_line)-1

        #Old code, implementations apparantly do not comply to Companion Standard
        #        P1_value=float(P1_line[P1_lastpos-9:P1_lastpos])
        #        P1_unit=P1_line[P1_lastpos-14:P1_lastpos-12]
        #Value is in next line
        P1_unit=P1_line[P1_lastpos-2:P1_lastpos]
        P1_raw = ser.readline()
        P1_str=str(P1_raw)
        P1_line=P1_str.strip()

        #self, id=None, type_id=None, type_desc=None, equipment_id=None, timestamp= None, meterreading=None, unit=None, valveposition=None
        if P1_channel==1:
            P1_channel_1.timestamp=P1_channel_timestamp
            P1_channel_1.meterreading=float(P1_line[1:10])
            P1_channel_1.unit=P1_unit
        elif P1_channel==2:
            P1_channel_2.timestamp=P1_channel_timestamp
            P1_channel_2.meterreading=float(P1_line[1:10])
            P1_channel_2.unit=P1_unit
        elif P1_channel==3:
            P1_channel_3.timestamp=P1_channel_timestamp
            P1_channel_3.meterreading=float(P1_line[1:10])
            P1_channel_3.unit=P1_unit
        elif P1_channel==4:
            P1_channel_4.timestamp=P1_channel_timestamp
            P1_channel_4.meterreading=float(P1_line[1:10])
            P1_channel_4.unit=P1_unit

    elif P1_line[4:10] == "24.2.1" and P1_Telegram:
        #Last hourly value delivered to client (DSMR v4)
        #eg. 0-1:24.2.1(101209110000W)(12785.123*m3)
        P1_channel=int(P1_line[2:3])
        P1_channel_timestamp="20"+P1_line[11:13]+"-"+P1_line[13:15]+"-"+P1_line[15:17]+" "+P1_line[17:19]+":"+P1_line[19:21]+":"+P1_line[21:23]
        P1_lastpos=len(P1_line)-1
        P1_line=P1_line[25:P1_lastpos]
        P1_lastpos=len(P1_line)
        P1_num_start = P1_line.find("(") +1
        P1_num_end = P1_line.find("*")
        P1_value=float(P1_line[P1_num_start:P1_num_end])        
        P1_unit=P1_line[P1_num_end+1:P1_lastpos]

        #self, id=None, type_id=None, type_desc=None, equipment_id=None, timestamp= None, meterreading=None, unit=None, valveposition=None
        if P1_channel==1:
            P1_channel_1.timestamp=P1_channel_timestamp
            P1_channel_1.meterreading=P1_value
            P1_channel_1.unit=P1_unit
        elif P1_channel==2:
            P1_channel_2.timestamp=P1_channel_timestamp
            P1_channel_2.meterreading=P1_value
            P1_channel_2.unit=P1_unit
        elif P1_channel==3:
            P1_channel_3.timestamp=P1_channel_timestamp
            P1_channel_3.meterreading=P1_value
            P1_channel_3.unit=P1_unit
        elif P1_channel==4:
            P1_channel_4.timestamp=P1_channel_timestamp
            P1_channel_4.meterreading=P1_value
            P1_channel_4.unit=P1_unit

    elif P1_line[4:10] == "24.4.0" and P1_Telegram:
        #Valve position (on/off/released)
        #eg. 0-1:24.4.0()
        #Valveposition defaults to '1'(=Open) if invalid value
        P1_channel=int(P1_line[2:3])
        P1_lastpos=len(P1_line)-1
        P1_value=P1_line[12:P1_lastpos].strip()
        if not isinstance(P1_value, int):
           P1_value=1
        if P1_channel==1:
            P1_channel_1.valveposition=P1_value
        elif P1_channel==2:
            P1_channel_2.valveposition=P1_value
        elif P1_channel==3:
            P1_channel_3.valveposition=P1_value
        elif P1_channel==4:
            P1_channel_4.valveposition=P1_value

    elif P1_line[0:1] == "" or P1_line[0:1] == " ":
        #Empty line
        P1_value=""
    elif P1_line[0:1] == "!":
        #end of P1 telegram
        if P1_Telegram and configdata.consolelogging:
            log_console()
            
        if P1_Telegram and configdata.databaselogging:
            log_database()
            
        P1_teller=0
        P1_Telegram=False        
    else:
        if P1_Telegram and configdata.consolelogging: 
            print ("Failed analysing P1 message, non recognized data found: '%s'" % P1_line )
      
