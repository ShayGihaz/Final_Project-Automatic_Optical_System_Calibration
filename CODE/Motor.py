'''
Written by Lev Galperin and Shay Gihaz
'''
import pythonnet
import clr

# Set up the .NET runtime environment
pythonnet.load()
clr.AddReference("System")
from System import Decimal


# Load the required assemblies
thorlabs_motion_control_cli_path = "C:\Program Files\Thorlabs\Kinesis/Thorlabs.MotionControl.DeviceManagerCLI.dll"

clr.AddReference(thorlabs_motion_control_cli_path)
thorlabs_motion_control_generic_motor_cli_path = "C:\Program Files\Thorlabs\Kinesis/Thorlabs.MotionControl.GenericMotorCLI.dll"
clr.AddReference(thorlabs_motion_control_generic_motor_cli_path)
thorlabs_motion_control_kcube_dcservo_cli_path = "C:\Program Files\Thorlabs\Kinesis/Thorlabs.MotionControl.KCube.DCServoCLI.dll"
clr.AddReference(thorlabs_motion_control_kcube_dcservo_cli_path)

# thorlabs_motion_control_kcube_dcservo_path = "C:\Program Files\Thorlabs\Kinesis/Thorlabs.MotionControl.KCube.DCServo.h"
# clr.AddReference(thorlabs_motion_control_kcube_dcservo_path)

# Import the required namespaces and types
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI, DeviceConfiguration
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo
from Thorlabs.MotionControl.GenericMotorCLI.Settings import MotorConfiguration
# from Thorlabs.MotionControl.KCube.DCServo import DCServo



class Motor():
    def __init__(self, serial_no):
        # here we need to setup the motors generals like the steps in the moovment and the manual calibration
        # Create an instance of KCubeDCServo class
        DeviceManagerCLI.BuildDeviceList()
        # Create an instance of KCubeDCServo class
        # DCServo.CC_SetMotorTravelLimits(serial_no,-5)
        self.device = KCubeDCServo.CreateKCubeDCServo(serial_no)

        # Connect to the device
        print(f"Opening device {serial_no}")
        self.device.Connect(serial_no)

        # Wait for the device settings to initialize
        self.device.WaitForSettingsInitialized(5000)

        # Load motor configuration
        motor_settings = self.device.LoadMotorConfiguration(serial_no,
                                                       DeviceConfiguration.DeviceSettingsUseOptionType.UseFileSettings)

        self.coordinate = self.device.Position
        #configuration = self.device.LoadMotorConfiguration(serial_no)

        pass


    def move(self, coordinate = 0, velocity = 20000):
        self.device.MoveTo(self.coordinate+Decimal(coordinate), velocity)
        self.coordinate += Decimal(coordinate)

    def move_exactly(self, pos = 0, velocity = 20000):
        self.device.MoveTo(pos, velocity)
        self.coordinate = pos




    def save_coordinte(self):
        self.cord = 1
        return self.cord

    def shutdown(self):
        self.device.Shutdown()
