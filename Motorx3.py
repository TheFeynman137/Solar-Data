#general setup////////////////////////////////////////////////////////////////////////////////////////////////////

import time, board, busio
import serial, pynmea2, requests,os
import adafruit_ads1x15.ads1115 as ADS
import RPi.GPIO as GPIO
from adafruit_ads1x15.analog_in import AnalogIn

writecount = 0
relaycount = 0
interval = 1 #seconds
writefreq = 60 #seconds
stopfreq = 60 #seconds
HTTPtimeout = 60 #seconds
error = 0 #error code set-up

#Relay Setup
GPIO.setup(4,GPIO.OUT)
GPIO.output(4,GPIO.HIGH)


#HTTP Setup
API_ENDPOINT = 'https://feynmaniot.com/post-esp-data333333.php'
API_KEY = "tPmAT5Ab3j7F9"


#ADC setup
VDAR1 = 10000 #resistor1 of voltage divider for 12V battery measurement
VDAR2 = 2000 #resistor2 of voltage divider for 12V battery measurement

#GPS Setup
latitude = 0
longitude = 0

#ESP32 Setup
Rawbatteryvolt = 0
RawRPM = 0



#main loop//////////////////////////////////////////////////////////////////////////////////////////////////////////////////
try:
    while True:

#count logic////////////////////////

        if writecount<=writefreq:
            writecount = writecount + interval
        else:
            writecount = 1

        if relaycount<=stopfreq:
            relaycount = relaycount + interval
        else:
            relaycount = 1

#ADC code///////////////////////////
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            ads=ADS.ADS1115(i2c)
            ads.gain = 2/3
            chan0=AnalogIn(ads, ADS.P0) #Oil Temperature
            chan1=AnalogIn(ads, ADS.P1) #Fuel Supply 
            chan2=AnalogIn(ads, ADS.P2) #Oil Pressure
            chan3=AnalogIn(ads, ADS.P3) #5V Header
            CV0 = chan0.voltage
            CV1 = chan1.voltage
            CV2 = chan2.voltage
            CV3 = chan3.voltage
        except:
            CV0 = 0.01
            CV1 = 0.01
            CV2 = 0.01
            CV3 = 0.01
            error = 1
            print('ADC failure')
            

        if CV0 <= 0.001:
            voltage0 = 0.001
        else:
            voltage0 = CV0

        if CV1 <= 0.001:
            voltage1 = 0.001
        else:
            voltage1 = CV1


        if CV2 <= 0.001:
            voltage2 = 0.001
        else:
            voltage2 = CV2

        if CV3 <= 0.001:
            voltage3 = 0.001
        else:
            voltage3 = CV3
    
        RawtempC = (voltage0 - 1.25)/0.005
        RawtempF = RawtempC*(9/5)+32
        Rawpress = voltage2*25 - 12.5
        header5V = voltage3
        Rawfuel= ((100*330)/90)*((header5V/voltage1)-1)

#GPS Code//////////////////////////////
        try:
            port1 = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00'  
            serialPort1 = serial.Serial(port1, baudrate = 115200, timeout = 0.5)
            str = serialPort1.readline().decode()
            if str.find('GGA') > 0:
                msg = pynmea2.parse(str)
                latitude = round(msg.latitude,8)
                longitude = round(msg.longitude,8)
            else:
                latitude = latitude
                longitude = longitude
        except:
            error = 2
            print('GPS comms failure')
            

#ESP32 Code/////////////////////////////
        a = b = 0
        #command ESP32 to write
        try:
            port2 = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'  
            serialPort2 = serial.Serial(port2, baudrate = 115200, timeout = 0.5)
            serialPort2.write(b"X")
            #read data from ESP32
            ESP32 = serialPort2.readline()
            ESP32 = ESP32.decode("utf-8","ignore")
            if len(ESP32) > 0 and ESP32[0] == "X":
                x, e, f  = ESP32.split(',')
                a = float(e)
                b = float(f)
                Rawbatteryvolt = a
                RawRPM = (b/4)*60
        except:
            error = 3
            print('ESP comms failure')
#Relay/////////////////////////////////////

        if relaycount == stopfreq:
            GPIO.output(4,GPIO.LOW)
        else:
            GPIO.output(4,GPIO.HIGH)
            

#Filters//////////////////////////////////
            
        if Rawbatteryvolt <= 20 and Rawbatteryvolt >=6:
            batteryvolt = round(Rawbatteryvolt,1)
        else:
            batteryvolt = 0.01

        if RawRPM <= 10000 and RawRPM >=0.01 and batteryvolt >=6:
            RPM = round(RPM,1)
        else:
            RPM = 0.01

        if Rawfuel >= 0.01 and Rawfuel <=150 and batteryvolt >=6:
            fuel = round(fuel,1)
        else:
            fuel = 0.01

        if Rawpress >=0.01 and Rawpress <=300 and batteryvolt >=6:
            press = round(press,1)
        else:
            press = 0.01

        if RawtempF >=10 and RawtempF <=500 and batteryvolt >=6:
            tempF = round(tempF,1)
        else:
            tempF = 0.01
        
#Output/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        if writecount ==1:
            try:
                Send = {'api_key':API_KEY,'batteryvolt':batteryvolt,'fuel':fuel,'press':press,'tempF':tempF,'RPM':RPM,'latitude':latitude,'longitude':longitude}
                response = requests.post(url = API_ENDPOINT,data = Send,timeout = HTTPtimeout)
                print(response.text)
            except:
                error = 4
                print('network connectivity failure')
        print('batteryvolt =',f'{batteryvolt:.1f}','V','fuel =',f'{fuel:.0f}','%','press =',f'{press:.1f}','psig','tempF =',f'{tempF:.1f}','F','RPM =',f'{RPM:.1f}','latitude =', f'{latitude:.6f}','longitude =',f'{longitude:.6f}','writecount =',writecount,'relaycount =',relaycount)
        time.sleep(interval)
finally:
    GPIO.cleanup()
