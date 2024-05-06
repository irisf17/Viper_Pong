#include <Arduino.h>
#include <Adafruit_DRV2605.h>
#include <Wire.h> //Used for I2C communications, enables us to use SDA and SCL pins
#include <Adafruit_TinyUSB.h> // If you use the onboard package of Seeed nRF52 Boards, the Serial function may not compile. The solution is to add the line "#include <Adafruit_TinyUSB.h>"



// -------- VIPER SWIPE SCRIPT ----------

// --- Script to receice byte packages from the Panda. The signals are not normalised. 
// The start value = 170, which is the package that includes the EMG signals, second bit from package indicates the size of the package.
// We want the package that is the size 10., The first 2 bits are then 170 10 x x x x x x EMGx x EMGx x. 
// Bits number 7 og 9 in the array are then the EMG signals.

boolean newData = false;
boolean signal_arr_flag = false;
boolean time_flag_m1 = true;
boolean time_flag_m2 = true;

const byte numBytes = 11;
int receivedBytes[numBytes];
int numReceived = 0;

float signal_arr[2];
int signal_diff = 0;
int abs_signal_diff = 0;


// ------- Need to update these values, using scaled MVC 80% --------
float MVC_S1 = 231*0.8;
float MVC_S2 = 231*0.8;
// ------------------------------------------------------------------


int delta_t_m1 = 0;
int delta_t_m2 = 0;

// initiate time 
unsigned long time_stamp_m1 = 0;
unsigned long time_stamp_m2 = 0;
int viper_delay_m1 = 0;
int viper_delay_m2 = 0;

unsigned long time_now_m1 = 0;
unsigned long time_now_m2 = 0;

// ----------------- for VIPER I2C communication ------------------------------
#define TCAADDR 0x70
Adafruit_DRV2605 drv;
// --- type of waveform ---
uint8_t effect = 47;

// constants for muscle 1
char PORT0 = 0;
char PORT1 = 1;
char PORT2 = 2;
int port_arr_m1[3] = {PORT0,PORT1,PORT2};
int indx_m1 = 0;
// constants for muscle 2
char PORT3 = 3;
char PORT4 = 4;
char PORT5 = 5;
int port_arr_m2[3] = {PORT3,PORT4,PORT5};
int indx_m2 = 0;

bool auto_cal_flag = true;
bool do_nth_flag_m1 = false;
bool do_nth_flag_m2 = false;
// ----------------- for VIPER I2C communication ------------------------------
void tcaselect(uint8_t i) {
  if (i > 7) return;
 
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();  
}


void setup() {
  Serial.begin(921600);
  Serial1.begin(921600);
  Wire.begin();

  delay(5000); //important to delay for the drivers to settle in!
    
  // --- PORT 0 ---
  tcaselect(PORT0);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 0:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 0 found...");
  }

  // ---- PORT 1 ----
  tcaselect(PORT1);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 1:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 1 found...");
  }

  // ---- PORT 2 ----
  tcaselect(PORT2);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 2:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 2 found...");
  }

  // ---- PORT 3 ----
  tcaselect(PORT3);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 3:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 3 found...");
  }
  
  // ---- PORT 4 ----
  tcaselect(PORT4);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 4:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 4 found...");
  }

  // ---- PORT 5 ----
  tcaselect(PORT5);
  if(!drv.begin()){
    /* There was a problem detecting the HMC5883 ... check your connections */
    Serial.print("Ooops, could not find DRV2605 on TCA port 5:" );
    Serial.println(" ... Check your wiring!" );
    while(1);
    }
  else{
    Serial.println("Driver port 5 found...");
  }

}

void init_LRA()
{
  // initalise the LRA after the calibration
  drv.setMode(DRV2605_MODE_INTTRIG);
  drv.selectLibrary(6);
  drv.useLRA();

  drv.writeRegister8(DRV2605_REG_CONTROL1, 0x93);
  drv.writeRegister8(DRV2605_REG_CONTROL2, 0xC5);
  drv.writeRegister8(DRV2605_REG_CONTROL3, 0x84);
  drv.writeRegister8(DRV2605_REG_CONTROL4, 0x20);

  drv.setWaveform(0, effect);  // play effect 
  drv.setWaveform(1, 0);       // end waveform
}

void start_calibration()
{
    // exit standby mode
  drv.writeRegister8(DRV2605_REG_MODE, 0x00);
  // LRA
  drv.writeRegister8(DRV2605_REG_FEEDBACK, 0x80);

  drv.useLRA();
    
  // set the voltages from driver to LRA
  drv.writeRegister8(DRV2605_REG_RATEDV, 0x7A); //rated voltage register
  drv.writeRegister8(DRV2605_REG_CLAMPV, 0xE3); //rated overdrive clamp register
  // setting the control registers
  drv.writeRegister8(DRV2605_REG_CONTROL1, 0x93);
  drv.writeRegister8(DRV2605_REG_CONTROL2, 0xC5);
  drv.writeRegister8(DRV2605_REG_CONTROL3, 0x84);
  drv.writeRegister8(DRV2605_REG_CONTROL4, 0x20);
  drv.setMode(DRV2605_MODE_AUTOCAL);
  
  drv.go();

  int8_t go = 1;
  int8_t i = 0;

  // Wait for autocalibration to finish
  do {
    go = drv.readRegister8(DRV2605_REG_GO);
    delay(100);
    ++i;
  } while (go == 1 && i < 100); //when GO bit changes to 0 the calibration has completed.

  // Calibration complete, read DIAG_RESULT register
  uint8_t diagResult = drv.readRegister8(DRV2605_REG_STATUS);
  delay(500);
  // Check if DIAG_RESULT bit is set (bit 7)
  if (diagResult & (1 << 7)) {
    // DIAG_RESULT bit is set
    Serial.println("DIAG_RESULT bit is set: Auto-calibration completed without faults.");
  } else {
    // DIAG_RESULT bit is not set
    Serial.println("DIAG_RESULT bit is not set: Auto-calibration completed with faults.");
  }
  // ------calibration is done-------
  // Serial.println("Auto calibration is done...");

  // ------grab values from calibration------
  uint8_t ACalComp = drv.readRegister8(DRV2605_REG_AUTOCALCOMP);
  uint8_t ACalBEMF = drv.readRegister8(DRV2605_REG_AUTOCALEMP);
  uint8_t BEMFGain = drv.readRegister8(DRV2605_REG_FEEDBACK);


  // ------write them to the registers----------
  // ------insert values from calibration---------
  drv.writeRegister8(DRV2605_REG_AUTOCALCOMP, ACalComp);
  drv.writeRegister8(DRV2605_REG_AUTOCALEMP, ACalBEMF);
  drv.writeRegister8(DRV2605_REG_FEEDBACK, BEMFGain);

  // ----- read values from ACalComp, ACalBEMF and BEMFGain------------
  // Serial.print("ACalComp: ");
  // Serial.println(ACalComp);

  // Serial.print("ACalBEMF: ");
  // Serial.println(ACalBEMF);

  // Serial.print("BEMFGain: ");
  // Serial.println(BEMFGain);
  delay(1000);
}


void recBytes() {
  static boolean recvInProgress = false;
  static byte ndx = 0;
  // --- first bit from panda ---
  byte startMarker = 170;

  int rb; // rb = received byte

  while (Serial1.available() > 0 && newData == false) {
      rb = Serial1.read();

      if (recvInProgress == true)
      {
          if (ndx != numBytes)
          {
            receivedBytes[ndx] = rb;
            ndx++;
          }
          else {
            recvInProgress = false;
            numReceived = ndx;
            ndx = 0;
            newData = true;
          }


      }
    else if (rb == startMarker)
    {
      recvInProgress = true;
    }
  }
}

void grabNewData() {
    if (newData == true) {
      // Serial.println("new data");
        // Serial.print("This just in ... ");
        // --- read the second bit from Panda ---
        if (receivedBytes[0] == 10)
        {

          // ----- grabbing raw data -----
          // signal_arr[0] = receivedBytes[8] * 256 + receivedBytes[7];
          // signal_arr[1] = receivedBytes[10] * 256 + receivedBytes[9];


          // ---- grabbing normalized data -----
          signal_arr[0] = (receivedBytes[8] * 256 + receivedBytes[7])*1.0/MVC_S1 * 100.0;
          signal_arr[1] = (receivedBytes[10] * 256 + receivedBytes[9])*1.0/MVC_S2 * 100.0;
          signal_arr_flag = true;
          
          // --- Normalize the signals ---
          // float s1_normal = s1_raw/MVC_S1 * 100.0;
          // float s2_normal = s2_raw/MVC_S2 *100.0;

          if (signal_arr[0] > 100)
          {
            signal_arr[0] = 100;
          }

          if (signal_arr[1] > 100)
          {
            signal_arr[1] = 100;
          }

          // Serial.print(signal_arr[0]);
          // Serial.print(' ');
          // Serial.println(signal_arr[1]);
          // delay(100);

        }
        newData = false;
    }
    else{
      signal_arr_flag = false;
    }
}



void do_sth_withDATA() // this function determines how the LRAs vibrate according to the muscle contraction
{
  if (signal_arr_flag == true)
  {
    bool do_nth_flag_m1 = false;
    bool do_nth_flag_m2 = false;
    // ------------- MUSCLE 1 ---------------
    // ------------- MUSCLE 2 ---------------
    if (time_flag_m1 == true || time_flag_m2 == true)
    {
      if (time_flag_m1 == true){time_stamp_m1 = millis();}
      if (time_flag_m2 == true){time_stamp_m2 = millis();}
      
      signal_diff = signal_arr[0] - signal_arr[1];
      // Serial.println(signal_diff);
      abs_signal_diff = abs(signal_diff);

      do_nth_flag_m1 = false;
      do_nth_flag_m2 = false;
      // --- below the threshold of the VIPER, nothing happens --- 
      if (signal_arr[0] > 0 && signal_arr[0] < 20 && time_flag_m1 == true){do_nth_flag_m1 = true;}//do nothing
      if (signal_arr[1] > 0 && signal_arr[1] < 20 && time_flag_m2 == true){do_nth_flag_m2 = true;} //do nothing
      // --- play the co-contraction pattern ---
      if (signal_arr[0] >= 20 && signal_arr[1] >= 20 && abs_signal_diff >= 0 && abs_signal_diff <= 20 && (time_flag_m1 == true || time_flag_m2 == true)) // CO-CONTRACTION
      {
        tcaselect(PORT0);
        drv.go();
        delay(10);
        tcaselect(PORT3);
        drv.go();
        viper_delay_m1 = 50;
        viper_delay_m2 = 50;
        do_nth_flag_m1 = true;
        do_nth_flag_m2 = true;
      }
      // --- swiping pattern for muscle 2 --- 
      if (do_nth_flag_m1 == false && signal_arr[0] >= 20 && time_flag_m1 == true)
      {
        tcaselect(port_arr_m2[indx_m1]);
        drv.go();
        indx_m1++;
        if (indx_m1 == 3){indx_m1 = 0;}
        viper_delay_m1 = (-1*signal_arr[0]) + 200 + ((1-(signal_arr[0]/100.0)) *500);
      }

      // --- swiping pattern for muscle 1 --- 
       if (do_nth_flag_m2 == false && signal_arr[1] >= 20 && time_flag_m2 == true)
      {
        tcaselect(port_arr_m1[indx_m2]);
        drv.go();
        indx_m2++;
        if (indx_m2 == 3){indx_m2 = 0;}
        viper_delay_m2 = (-1*signal_arr[1]) + 200 + ((1-(signal_arr[1]/100.0)) *500);
      }
      // --- flags to control the waiting for the LRAs without stopping the running of the code ---
      if (time_flag_m1 == true){time_flag_m1 = false;}
      if (time_flag_m2 == true){time_flag_m2 = false;}
    }
  }

  // --- instead of delaying the whole code, these if statements control the waiting time of the LRAs for the next vibration pattern ---
  time_now_m1 = millis();
  delta_t_m1 = time_now_m1 - time_stamp_m1;
  if (delta_t_m1 > viper_delay_m1)
  {
    time_flag_m1 = true;
  }
  time_now_m2 = millis();
  delta_t_m2 = time_now_m2 - time_stamp_m2;
  if (delta_t_m2 > viper_delay_m2)
  {
    time_flag_m2 = true;
  }
}


void loop() {
  // ---- perform calibration once ------
  while (auto_cal_flag == true){

    // Serial.println("Auto calibration in process....");

    // ----- start the calibration and initalization of LRAs -----
    // --- for muscle 1 ---
    // ---- PORT 0 ----
    tcaselect(PORT0);
    start_calibration();
    init_LRA();
    // ---- PORT 1 ----
    tcaselect(PORT1);
    start_calibration();
    init_LRA();
    // ---- PORT 2 ----
    tcaselect(PORT2);
    start_calibration();
    init_LRA();

    // --- for muscle 2 ---
    // ---- PORT 3 ----
    tcaselect(PORT3);
    start_calibration();
    init_LRA();
    // ---- PORT 4 ----
    tcaselect(PORT4);
    start_calibration();
    init_LRA();
    // ---- PORT 5 ----
    tcaselect(PORT5);
    start_calibration();
    init_LRA();

    auto_cal_flag = false;
  }

// --- process EMG data ---
  recBytes();
  grabNewData();
  // --- output the following pattern ---
  do_sth_withDATA();
}
