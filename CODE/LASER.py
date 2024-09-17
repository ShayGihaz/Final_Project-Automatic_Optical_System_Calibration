# This file is an API to work and send commands to the Laser device.
from NKTP_DLL import *
import time

class Laser:
    # Class to operate the Laser:

    # This function create the object of the laser.
    def __init__(self, COM, Serial=15, type=0):
        self.COM = COM
        self.Serial = Serial
        self.type = type  # SuperK EXTREME

    def send_TO_Register(self, reg, val, size=8):
        #  This function get the relevant register and the value to send to him.
        if (size == 16):
            ans = registerWriteU16(self.COM, self.Serial, reg, val, self.type) 
        else:
            ans = registerWriteU8(self.COM, self.Serial, reg, val, self.type)

    def emission(self, value):
        # Function 1: Laser Emission.
        # Laser On/Off, values: On = '1 or Positive number' , OFF = '0 or Negative number'.
        if (value <= 0):
            result = self.send_TO_Register(0x30, 0)
            if (result == 0):
                print('Laser emission is Off.\n')
        else:
            result = self.send_TO_Register(0x30, 3)
            if (result == 0):
                print('Laser emission is On.\n')
    # End of laser_Emission function.

    def setup(self, value):
        # Function 2: Laser Setup.
        # Values Options are:
        # 0: Constant current mode.
        # 1: Constant power mode.
        # 2: Externally modulated current mode.
        # 3: Externally modulated power mode.
        # 4: External feedback mode (Power Lock).
        values_Options = [0, 1, 2, 3, 4]
        if (value in values_Options):
            result = self.send_TO_Register(0x31, value)
            if (result == 0):
                if (value == 0):
                    print('Laser Setup: Constant current mode.')
                if (value == 1):
                    print('Laser Setup: Constant power mode.')
                if (value == 2):
                    print('Laser Setup: Externally modulated current mode.')
                if (value == 3):
                    print('Laser Setup: Externally modulated power mode.')
                if (value == 4):
                    print('Laser Setup External feedback mode (Power Lock).')
        else:
            print("Wrong value, Only the values: '0','1','2','3','4'.'")
    # End of laser_Setup function.

    def powerLevel(self, value):
        # Function 3: Laser Power Level.
        # INPUT: value between 6-100.
        # Set the laser power level.
        # Values in permile (‰).
        setpoint_val = int(value*10)
        if (1):
            result = self.send_TO_Register(0x37, setpoint_val, size=16)
            if (result == 0):
                print('The Laser Power Level is set to: ' + str(value) + '%\n')
        else:
            print('Bad values, Only between 0 to 100.')
    # End of laser_Power_Level function.

    def pulsePickerRation(self, value):
        # Function 4: Pulse Picker Value.
        # Set the laser setting rep rate.
        # Values in from 1 to 40.
        # Values meaning - Rape rate divider:
        values_MHz = {1: '78.56MHz', 2: '39.28MHz', 3: '29.19MHz', 4: '19.64MHz', 5: '15.71MHz',
                    6: '13.09MHz', 7: '11.22MHz', 8: '9.821MHz', 9: '8.729MHz', 10: '7.856MHz',
                    12: '6.547MHz', 14: '5.612MHz', 16: '4.910MHz', 18: '4.365MHz', 20: '3.928MHz',
                    22: '3.571MHz', 25: '3.143MHz', 27: '2.910MHz', 29: '2.709MHz', 32: '2.455MHz',
                    34: '2.311MHz', 37: '2.123MHz', 40: '1.964MHz'}
        # Good values options:
        if (value in values_MHz.keys()):
            result = self.send_TO_Register(0x34, value)
            if (result == 0):
                print('The Rep rate is set to: ' + values_MHz[value] + '.')
        else:
            print('Bad values, See descreption of the function for good values.')
    # End of laser_Pulse_Picker_Ratio function.

    def watchdogInterval(self, value):
        # This function set to automatically shut-off the laser emission if the connection with the laser will lost.
        # If the value is 0 the feature is disable
        if ((value >=0) and (value <256)):
            result = self.send_TO_Register(0x34, value, size=8)
            if (result == 0):
                if (value == 0):
                    print("The Watchdog interval feautre is disable.");
                else:
                    print("If the communication is lost the laser emittion will stop after" + value + " seconds.");
        else:
            print("Wrong values for the function! Please enter a number between 0 to 255.")

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------

# For Our checking:
if __name__ == "__main__":
    # Checks:
    Laser1 = Laser('COM6')
    Laser1.emission(0)
    for p in range(6,100,1):
        Laser1.powerLevel(p)
        time.sleep(1)
    # Laser1.pulsePickerRation(22)
    result = registerWriteU8('COM6', 15, 0x37, 60, -1)
    print('Setting power level - Extreme:', RegisterResultTypes(result))

# Endo of 'LASER.py' file.