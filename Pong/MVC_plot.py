from threading import Thread
import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import copy
import numpy as np

'''
This code reads raw EMG from the Panda with a serial connection.
Provides a live plot to visualise the EMG signals.
The signals are raw.
'''


# --- A class created to read EMG values from the Panda using serial. and insert the values into lists for live plotting  ---
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
        
        self.isRun = True
        print("Application is running")
        self.Received = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.x = 0
        self.y = 0

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

    def getSerialData(self, frames, s1_arr, s2_arr):
        ''' 
        A function used to read the values from the serial connection.
        Appends the raw EMG signals for muscle 1 and 2 to lists
        '''
        # print('trying to get data...')
        if(self.serialConnection.isOpen() == True):
            # print("Serial is open checked...")
            # print(self.rawData)
            # --- read first bit from Panda ---
            if((self.rawData[0]) == 170):
                # --- read second bit from Panda ---
                if(self.rawData[1] == 10):
                    # print("Values here...")
                    # print(self.rawData)
                    # --- so that the 3 values in our plots will be synchronized to the same sample time ---
                    privateData = copy.deepcopy(self.rawData[:])    
                    
                    #data1 = privateData[4:6]
                    data1 = privateData[8:10]
                    value1,  = struct.unpack(self.dataType, data1)
                    
                    #data2 = privateData[6:8]
                    data2 = privateData[10:12]
                    value2,  = struct.unpack(self.dataType, data2)
                    # --- filter out unwanted values, a bug from panda to send 20 20 packages ---
                    if value1 != 20:
                        s1_arr.append(value1)
                    if value2 != 20:
                        s2_arr.append(value2)

                    
                    plt.cla()
                    plt.plot(s1_arr, label='Signal 1')
                    plt.plot(s2_arr, label='Signal 2')
                    plt.title("EMG signals")
                    plt.legend(loc = 'upper left')

                    value_string = str(value1) + " " + str(value2)
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
            time.sleep(0.5)
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

# --- global variables ----
plt.style.use('fivethirtyeight')

def main():
    #df = pd.DataFrame([{'Flex' : 0, 'Extend' : 0}] )
    
    portName = '15'     # for windows users, string is in class "COM"
    #portName = '/dev/ttyUSB0'
    # baudRate = 1000000
    baudRate = 921600
    maxPlotLength = 100000
    # --- number of plots in 1 graph ---
    numPlots = 2          
    # --- number of bytes of 1 data point ---  
    dataNumBytes = 2        

    # --- initializes all required variables ----
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)   

     # --- starts background thread ---
    s.readSerialStart()                                              
    s.openSerial(portName)

    # --- initialize lists for the muscle signals ---
    s1_arr, s2_arr = [], []
    
    # --- live plot of the raw EMG signals ---
    anim = animation.FuncAnimation(plt.gcf(), s.getSerialData, fargs = (s1_arr, s2_arr), interval=0, cache_frame_data=False) #interval is in ms 
    
    plt.tight_layout()
    plt.show()


    print("End of live plot")

    # --- close the serial connection ---
    s.close()

    # --- print the raw EMG signals for muscle 1 and 2 ---
    print(f"MVC signal 1: {max(s1_arr)}")
    print(f"MVC signal 2: {max(s2_arr)}")
    # print("final results")

    # when plt.is closed, prenta út mvc fyrir signal 1 og signal 2

if __name__ == '__main__':
    main()