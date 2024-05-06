#!/usr/bin/env python

from threading import Thread
# from pynput.keyboard import Key, Controller
import pyautogui

import serial
import time
import collections
from matplotlib import style
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import struct
import copy
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as Tk
from tkinter.ttk import Frame
import pandas as pd
# import crc
import numpy as np
import sys
import keyboard as k

'''
This code reads raw EMG from the Panda with a serial connection.
The signals are saved into a shared file, and then are used to control the game single player pong written in pong_version4_sidebar.py. The signals are raw.
'''

# --- A class created to read EMG values from the Panda using serial ---
class serialPlot:
    def __init__(self, serialPort = 'COM15', serialBaud = 921600, plotLength = 100, dataNumBytes = 2, numPlots=2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(14)
        self.flexThreshold = 0;
        self.extendThreshold = 0;
        self.dataType = None
        self.Data1 = bytearray(2)
        self.Data2 = bytearray(2)
        if dataNumBytes == 2:
            self.dataType = 'h'     # 2 byte integer
        elif dataNumBytes == 4:
            self.dataType = 'f'     # 4 byte float
        self.data1 = np.array([0])
        self.data2 = np.array([0])
        self.record = False
        
        #self.data1.append(collections.deque([0] * plotLength, maxlen=plotLength))
        #self.data2.append(collections.deque([0] * plotLength, maxlen=plotLength))
        self.isRun = True
        print("Application is running")
        self.Received = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.x = 0
        self.y = 0

        #self.df = df
        
        #self.csvData = []

        self.serialConnection = serial.Serial()

    def readSerialStart(self):
        ''' 
        A function that starts the serial threading
        '''
        #if self.thread == None:
        self.thread = Thread(target=self.backgroundThread)
        self.thread.start()
            # Block till we start receiving values
            
            # while(self.serialConnection.isOpen() == False):
                # time.sleep(0.1)
            # self.serialConnection.reset_input_buffer()
            # while self.isReceiving != True:
                # #self.serialConnection.write(b'\xaa\x06\xb0\x14\x1e\x11\x32\x10\x84\xb5')
                # time.sleep(0.1)
                
    def openSerial(self, comport):
        ''' 
        A function that uses try, except blocks to open the serial code
        outputs an error code if unsuccessful
        '''
        print('Trying to connect to: ' + str("COM"+comport) + ' at ' + str(self.baud) + ' BAUD.')
        try:
            self.serialConnection.baudrate = self.baud
            self.serialConnection.port = str("COM"+comport) #self.port
            self.serialConnection.bytesize = serial.EIGHTBITS
            self.serialConnection.parity = serial.PARITY_NONE
            self.serialConnection.stopbits = serial.STOPBITS_ONE
            self.serialConnection.timeout = None
            #self.serialConnection.close()
            self.serialConnection.close()
            self.serialConnection.open()
            
        except:
            print("Failed to connect with " + str(self.port) + ' at ' + str(self.baud) + ' BAUD.')
        print('Port Open')
        
        print('Connected to ' + str(self.port) + ' at ' + str(self.baud) + ' BAUD.')

        self.serialConnection.write(b'\xaa\x08\xb1\x10\x7d\x13\x22\x00\x32\x00\x0a\xed') # set sensory feedback to 50
        #self.serialReference.serialConnection.write(b'\xaa\x08\xb1\x10\x7d\x13\x22\x00\x0A\x00\x19\x2d') # set sensory feedback to 10

    def getSerialData(self, s1_arr, s2_arr):
        ''' 
        A function used to read the values from the serial connection.
        Appends the raw EMG signals for muscle 1 and 2 to lists
        '''
        # print('trying to get data...')
        if(self.serialConnection.isOpen() == True):
            # print("Serial is open checked...")
            # print(self.rawData)
            
            if((self.rawData[0]) == 170): # & self.rawData[2] == 177
                if(self.rawData[1] == 10):
                    # print("Values here...")
                    # print(self.rawData)
                    privateData = copy.deepcopy(self.rawData[:])    # so that the 3 values in our plots will be synchronized to the same sample time
                    
                    #data1 = privateData[4:6]
                    data1 = privateData[8:10]
                    value1,  = struct.unpack(self.dataType, data1)
                    
                    #data2 = privateData[6:8]
                    data2 = privateData[10:12]
                    value2,  = struct.unpack(self.dataType, data2)

                    s1_arr.append(value1)
                    s2_arr.append(value2)

                    if s1_arr[-1] == 20 and s2_arr[-1] == 20:
                        value_string = str(s1_arr[-3]) + " " + str(s2_arr[-3])
                    else:
                        value_string = str(s1_arr[-1]) + " " + str(s2_arr[-1])
                  
                    print(str(value1) + " " + str(value2))

                    return value_string
                else:
                   self.serialConnection.reset_input_buffer()
            else:
               self.serialConnection.reset_input_buffer()

    def backgroundThread(self):
        ''' 
        A function that retrieve data with a background thread
        '''
        
        while(self.serialConnection.isOpen() == False):
            time.sleep(0.2)
        self.serialConnection.reset_input_buffer()
        print("Port is open")

        while (self.isRun == True):
            try:
                #self.serialConnection.seek(0,0)
                self.serialConnection.readinto(self.rawData)
            except:
                print("Unable to read serial")
                break
    
    def close(self):
        ''' 
        A function that closes the serial connection
        '''
        self.isRun = False
        self.thread.join()
        #self.thread = None
        self.serialConnection.write(b'\xaa\x08\xb1\x10\x7d\x13\x22\x00\x00\x00\x1f\x8d') # set sensory feedback to 0
        
        time.sleep(1)
        
        self.serialConnection.close()
        print('Disconnected...')
        # df = pd.DataFrame(self.csvData)
        #df.to_csv('/home/rikisenia/Desktop/data.csv')


# Maximum Voluntary Contraction for signal 1 and 2
# MVC_S1 = 110*0.8
# MVC_S2 = 249*0.8

# def normalise(signal1, signal2):
#     s1_normal = int(signal1/MVC_S1 *100)
#     if s1_normal > 100:
#         s1_normal = 100
#     s2_normal = int(signal2/MVC_S2 *100)
#     if s2_normal > 100:
#         s2_normal = 100
#     # Write the normalised values to a file
#     with open("shared_values_normal.csv", "a") as file:
#         file.write(f"{s1_normal}\n{s2_normal}\n")

#     return s1_normal, s2_normal


def raw_to_shared(signal1, signal2):
    '''
    A function that sends the raw muscle signals to a shared file called shared_values_raw.csv
    '''
    # Write the raw values to a file
    with open("shared_values_raw.csv", "a") as file:
        file.write(f"{signal1}\n{signal2}\n")



def main():
    #df = pd.DataFrame([{'Flex' : 0, 'Extend' : 0}] )
    
    portName = '15'     # for windows users, string is in class "COM"
    #portName = '/dev/ttyUSB0'
    # baudRate = 1000000
    baudRate = 921600
    maxPlotLength = 100000
    numPlots = 2            # number of plots in 1 graph
    dataNumBytes = 2        # number of bytes of 1 data point
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)   # initializes all required variables

    s.readSerialStart()                                               # starts background thread
    s.openSerial(portName)

    s1_arr, s2_arr = [0,0,0], [0,0,0]

    # with open("shared_values_normal.csv", "w"):
        # pass 

    # --- cleaning the file by opening it with w and doing nothing, it erases everything in it. ---
    with open("shared_values_raw.csv", "w"):
        pass  # This block does nothing, it's just to open and close the file

    while True:
        value_str = s.getSerialData(s1_arr, s2_arr)

        if value_str:
            s1, s2 = value_str.split()
            # raw values
            s1 = int(s1)
            s2 = int(s2)
            # print(f"Return values: {s1}, {s2}")
            # num_s1 = int(s1)
            # num_s2 = int(s2)

            # norm_s1, norm_s2 = normalise(num_s1, num_s2)
            # print(f"normalised {norm_s1}, {norm_s2}")

            # save the raw signals to a shared file
            raw_to_shared(s1, s2)



        time.sleep(0.02)
        # --- press q to stop the script ---
        if k.is_pressed('q'):
            break

    print("end of program")
    s.close()


if __name__ == '__main__':
    main()