from os import system
import threading
import csv
import time, datetime
import requests

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
    checkpoint = config.config_read()["competition"]["checkpoint"] #get current checkpoint
    checkpointteam = config.config_read()["competition"]["checkpointteam"] #get current checkpointteam

    data_for_file = []
    for tup in data:
        if source_type == "RFID":
            RFID_datetime = tup[0]
            RFID_tag = tup[1]
            RFID_rss = tup[2]
            RFID_team = RFIDtag_to_team(RFID_tag)

            data_temp = (RFID_datetime, RFID_tag, RFID_team, RFID_rss, checkpoint, checkpointteam, source_type)
            data_for_file.append(data_temp)


        elif source_type == "webapp":
            webapp_datetime = tup[0]
            webapp_team = tup[1]

            data_temp = (webapp_datetime, "Na", webapp_team, "Na", checkpoint, checkpointteam, source_type)
            data_for_file.append(data_temp)

        else:
            return None
 
    filename = config.config_read()["system"]["filename_registration"] #get file_name from config
    with open(filename,'a') as f: #write buffer to file
        writer = csv.writer(f)
        writer.writerows(data_for_file)


def cloud_synchronization():
    url = "http://www.kite.com"
    
    config_all = config.config_read()
    timeout = config_all['system']['update_interval']
    try:
        request = requests.get(url, timeout=timeout)
        config_all["system"]["internet"] = "TRUE"       
    except (requests.ConnectionError, requests.Timeout) as exception:
        config_all["system"]["internet"] = "FALSE"
    config.config_write(config_all)



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
            
            save_data(buffer_save, "RFID") #write buffer data to function save data
            RFID.RFID.RFID.buffer = list(set(RFID.RFID.RFID.buffer)-set(buffer_save)) #remove saved data from the buffer of the RFID class

        # buffer webapp to file    
        if len(webapp.webapp.webserver.buffer) > 0: # If the buffer is not empty
            buffer_save = webapp.webapp.webserver.buffer #save buffedata to local variable
            
            save_data(buffer_save, "webapp") #write buffer data to function save data
            webapp.webapp.webserver.buffer = list(set(webapp.webapp.webserver.buffer)-set(buffer_save)) #remove saved data from the buffer of the webapp
       
        cloud_synchronization() # send all data to the cloud

        time.sleep(update_interval) #wait update interval
        


if __name__ == '__main__':
    config.config_create() #create config file if absent
    on_boot() #action that needs to happen on boot of script
    threading.Thread(target=flaskThread).start() #start theard for webserver
    threading.Thread(target=RFIDThread).start() #start thread for interaction with RFID reader
    threading.Thread(target=bufferloop_thread).start() #start thread for redaing buffers
    
    
    