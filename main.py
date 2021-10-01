from datetime import datetime
from os import system
import threading
import csv
import time
import requests
import pymysql.cursors

import webapp.webapp #local webserver for entering manual data
import RFID.RFID #RFID reader interaction
import config #import the config of the app

def on_boot():
#    print('boot')
    config_all = config.config_read()
    config_all['system']['id'] = getserial()
    config.config_write(config_all)

def getserial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"
 
  return cpuserial

def RFIDtag_to_team(RFIDtag):
    RFIDtag_RFIDtag_list = []
    RFIDtag_team_list = []
    
    filename = config.config_read()["system"]["filename_RFIDtagToTeam"] #get file_name from config
    with open(filename, 'r') as file:
        file_reader = csv.reader(file, delimiter = ',')
        for row in file_reader:
            RFIDtag_RFIDtag_list.append(row[0])
            RFIDtag_team_list.append(row[1])
    
    try:
        RFID_to_team_index = RFIDtag_RFIDtag_list.index(RFIDtag)
        team = RFIDtag_team_list[RFID_to_team_index] 
#        print(team)
    except ValueError:
        team = 000 
#        print(team)
    
    return(team)


def save_data(data, source_type): #function to save data from memory to file
    ETAPPE_VOLGNUMMER = config.config_read()["competition"]["ETAPPE_VOLGNUMMER"] #huidige etappe
    EVENEMENT_ID = config.config_read()["competition"]["EVENEMENT_ID"] #huidig evenement
    LOCATIE_ID = config.config_read()["competition"]["LOCATIE_ID"] #huidige locatie
    checkpointteam = config.config_read()["competition"]["checkpointteam"] #get current checkpointteam

    data_for_file = []
    for tup in data:
        if source_type == "AUTO":
            RFID_datetime = tup[0]
            RFID_tag = tup[1]
            RFID_rss = tup[2]
            RFID_team = RFIDtag_to_team(RFID_tag)

            data_temp = (RFID_datetime, RFID_tag, RFID_team, RFID_rss, ETAPPE_VOLGNUMMER, EVENEMENT_ID, LOCATIE_ID, checkpointteam, source_type, "no_sync")
            data_for_file.append(data_temp)


        elif source_type == "MANUAL":
            webapp_datetime = tup[0]
            webapp_team = tup[1]

            data_temp = (webapp_datetime, "Na", webapp_team, "Na", ETAPPE_VOLGNUMMER, EVENEMENT_ID, LOCATIE_ID, checkpointteam, source_type, "no_sync")
            data_for_file.append(data_temp)

        else:
            return None
 
    filename = config.config_read()["system"]["filename_registration"] #get file_name from config
    with open(filename,'a', newline= "") as f: #write buffer to file
        writer = csv.writer(f)
        writer.writerows(data_for_file)


def cloud_synchronization():
    # test internet verbinding
    url_test = "https://www.google.com"
    
    config_all = config.config_read()
    timeout = config_all['system']['update_interval']
    try:
        request = requests.get(url_test, timeout=timeout)
        config_all["system"]["internet"] = "TRUE"       
    except (requests.ConnectionError, requests.Timeout) as exception:
        config_all["system"]["internet"] = "FALSE"
    config.config_write(config_all)

    
    # verbinding met de database
    connection = pymysql.connect(host=config.config_read()["database"]["host"],
                             user=config.config_read()["database"]["user"],
                             password=config.config_read()["database"]["password"],
                             database=config.config_read()["database"]["database"],
                             charset=config.config_read()["database"]["charset"],
                             cursorclass=pymysql.cursors.DictCursor)

    filename = config_all["system"]["filename_registration"] #get file_name from config
    with open(filename,'r') as f: #write buffer to file
        csv_reader = csv.reader(f, delimiter=',')
        lines = list(csv_reader)

        for row in range(len(lines)):
            if lines[row]:
                EVENEMENT_ID = lines[row][5]
                ETAPPE_VOLGNUMMER = lines[row][4]
                LOCATIE_ID = lines[row][6]
                DOORKOMSTTIJD = lines[row][0]
                STARTNUMMER = lines[row][2]
                DOORKOMST_TYPE = lines[row][8]
                status = lines[row][9]

                if status == "no_sync":
                    print("to sync")
                    if DOORKOMST_TYPE == "MANUAL":
                        try:
                            sql = """
                            CALL doorkomst_chip(%s,%s,%s,%s, @rowCount)
                            """
                        
                            cursor = connection.cursor()
                            cursor.execute(sql, (EVENEMENT_ID, ETAPPE_VOLGNUMMER, STARTNUMMER, DOORKOMSTTIJD))
                            connection.commit()

                            sql_2 = """
                            Select @rowCount;
                            """
                        
                            cursor.execute(sql_2)
                            connection.commit()
                            result = cursor.fetchone()
                            print(list(result.values())[0])
                            cursor.close()
                            if list(result.values())[0] != 0:
                                lines[row][9] = "sync"

                        except:
                            print("Failed to insert record into table")

                    if DOORKOMST_TYPE == "AUTO":
                        try:
                            sql = """
                            CALL doorkomst_chip(%s,%s,%s,%s, @rowCount)
                            """
                        
                            cursor = connection.cursor()
                            cursor.execute(sql, (EVENEMENT_ID, ETAPPE_VOLGNUMMER, STARTNUMMER, DOORKOMSTTIJD))
                            connection.commit()

                            sql_2 = """
                            Select @rowCount;
                            """
                        
                            cursor.execute(sql_2)
                            connection.commit()
                            result = cursor.fetchone()
                            print(list(result.values())[0])
                            cursor.close()
                            if list(result.values())[0] != 0:
                                lines[row][9] = "sync"

                        except:
                            print("Failed to insert record into table")
    f.close()


    with open(filename,'w', newline= "") as f: 
        writer = csv.writer(f)
        writer.writerows(lines)
    f.close
    
                
    with connection.cursor() as cursor:
        try:
            # Read a single record
            sql = """
            SELECT LE.ETAPPE_VOLGNUMMER, ET.ETAPPE_NAAM, LE.MAN_VROUW 
            FROM `EVENEMENTEN` E 
            JOIN `LOOPROUTES` L on E.LOOPROUTE_ID=L.LOOPROUTE_ID
            JOIN `LOOPROUTES_ETAPPES` LE on L.LOOPROUTE_ID=LE.LOOPROUTE_ID
            JOIN `ETAPPES` ET ON LE.ETAPPE_ID=ET.ETAPPE_ID
            WHERE `EVENEMENT_ID`=5
            """
            
#            "SELECT `ETAPPE_ID`, `ETAPPE_NAAM`, `LOCATIE_ID_FINISH` FROM `ETAPPES`"
#              "SELECT * FROM `EVENEMENTEN` JOIN `LOOPROUTES` on `EVENEMENTEN.LOOPROUTE_ID` = `LOOPROUTES.LOOPROUTE_ID` JOIN `LOOPROUTES_ETAPPES` on `LOOPROUTES.LOOPROUTE_ID` = `LOOPROUTES_ETAPPES.LOOPROUTE_ID` JOIN `ETAPPES` ON `LOOPROUTES_ETAPPES.ETAPPE_ID` = `ETAPPES.ETAPPE_ID` WHERE `EVENEMENTEN.EVENEMENT_ID` = '5'"
            cursor = connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            
#            print(result)
            result_list = []
            for row in result:
                result_list.append(row)
            config_all = config.config_read()
            config_all["competition"]["checkpoint_list"] = result_list
            config.config_write(config_all)
        except:
                print("Failed to read record from table")


def flaskThread(): #function to start local webserver
    webapp.webapp.app.run(host="0.0.0.0", threaded=True)


# start and keep reading RFID reader from the class RFID
def RFIDThread():  
    RFID.RFID.RFID().start()


# read the buffer of the RFID class
def bufferloop_thread():  
    while True: #start endless loop

        update_interval = config.config_read()["system"]["update_interval"] #get current update interval

        # buffer RFID to file
        if len(RFID.RFID.RFID.buffer) > 0: # If the buffer is not empty
            buffer_save = RFID.RFID.RFID.buffer #save buffedata to local variable
            
            save_data(buffer_save, "AUTO") #write buffer data to function save data
            RFID.RFID.RFID.buffer = list(set(RFID.RFID.RFID.buffer)-set(buffer_save)) #remove saved data from the buffer of the RFID class

        # buffer webapp to file    
        if len(webapp.webapp.webserver.buffer) > 0: # If the buffer is not empty
            buffer_save = webapp.webapp.webserver.buffer #save buffedata to local variable
            
            save_data(buffer_save, "MANUAL") #write buffer data to function save data
            webapp.webapp.webserver.buffer = list(set(webapp.webapp.webserver.buffer)-set(buffer_save)) #remove saved data from the buffer of the webapp
        
        try:
            cloud_synchronization() # send all data to the cloud
        except:
            print(datetime.now(), "Failed cloud synchronization")

        time.sleep(update_interval) #wait update interval
        
if __name__ == '__main__':
    config.config_create() #create config file if absent
    print('step 1')
    time.sleep(2)
    on_boot() #action that needs to happen on boot of script
    print('step 2')
    time.sleep(2)
    threading.Thread(target=flaskThread).start() #start theard for webserver
    print('step 3')
    time.sleep(2)
    threading.Thread(target=RFIDThread).start() #start thread for interaction with RFID reader
    print('step 4')
    time.sleep(2)
    threading.Thread(target=bufferloop_thread).start() #start thread for redaing buffers