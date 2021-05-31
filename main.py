import threading
import csv
import time, datetime

import webapp.webapp #local webserver for entering manual data
import RFID.RFID #RFID reader interaction
import config #import the config of the app


def save_data(data): #function to save data from memory to file
    checkpoint = config.config_read()["competition"]["checkpoint"] #get current checkpoint
    checkpointteam = config.config_read()["competition"]["checkpointteam"] #get current checkpointteam

    data = [list(tup)+[checkpoint, checkpointteam] for tup in data] #add checkpoint and checkpointteam to dataset in buffer
    
    file_name = config.config_read()["system"]["file_name"] #get file_name from config
    with open(file_name,'a') as f: #write buffer to file
        writer = csv.writer(f)
        writer.writerows(data)


def cloud_synchronization():
    pass


def flaskThread(): #function to start local webserver
    webapp.webapp.app.run(host="0.0.0.0", threaded=True)


# start and keep reading RFID reader from the class RFID
def RFIDThread():  
    RFID.RFID.RFID().start()


# read the buffer of the RFID class
def bufferloop_thread():  
    while True: #start endless loop
        cloud_synchronization() #function for cloud synchronization

        update_interval = config.config_read()["system"]["update_interval"] #get current checkpoint

        # buffer RFID to file
        if len(RFID.RFID.RFID.buffer) > 0: # If the buffer is not empty
            buffer_save = RFID.RFID.RFID.buffer #save buffedata to local variable
            
            save_data(buffer_save) #write buffer data to function save data
            RFID.RFID.RFID.buffer = list(set(RFID.RFID.RFID.buffer)-set(buffer_save)) #remove saved data from the buffer of the RFID class

        # buffer webapp to file    
        if len(webapp.webapp.webserver.buffer) > 0: # If the buffer is not empty
            buffer_save = webapp.webapp.webserver.buffer #save buffedata to local variable
            
            save_data(buffer_save) #write buffer data to function save data
            webapp.webapp.webserver.buffer = list(set(webapp.webapp.webserver.buffer)-set(buffer_save)) #remove saved data from the buffer of the webapp
       
        cloud_synchronization() # send all data to the cloud

        time.sleep(update_interval) #wait update interval
        


if __name__ == '__main__':
    config.config_create() #create config file if absent
    threading.Thread(target=flaskThread).start() #start theard for webserver
    threading.Thread(target=RFIDThread).start() #start thread for interaction with RFID reader
    threading.Thread(target=bufferloop_thread).start() #start thread for redaing buffers
    
    
    