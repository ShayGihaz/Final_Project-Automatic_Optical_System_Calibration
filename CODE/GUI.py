# This file contains the Graphical user interface and delivers the requests from the user to devices.
from OSA import OSA
from LASER import Laser
from Operator import getSweepResults, runSample, setConfig, makedirectory, noiseMeasurments
from Interactive_Graph import interactiveGraph
from multiprocessing import Process, freeze_support , Queue
from json import load, dump
from time import sleep
import time
import os
import shutil
import threading
import tkinter.messagebox as tkm
import PySimpleGUI as sg
import subprocess
from Main_calibration import start_CAl_main
# import Main_calibration

# try:
#     import serial
# except:
#     subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'serial'])
# import serial.tools.list_ports
# def printPortList():
#     ports = list(serial.tools.list_ports.comports())
#     # ports = list(serial.tools.list_ports.comports())
#     for port in ports:
#         print(port.device)

#---------------------------------------------------------------------------------------------------------------------------

# Globals:
global layouts
global cwd
global connectionsDict
#global osa
#global laser
global isConnected
global debugMode
global status
global getConnectionsText
global getSamplesText
global getTestErrorText
isConnected = False # Until first connection
debugMode = False
status = "The devices are not connected"
getConnectionsText = "If you don't succed to connect you can work in 'Debug Mode'"
getSamplesText = "Connect to devices first or work in 'Debug Mode'"
getTestErrorText = ""
graphs_pids = []
# sg.theme_previewer()

# Initial reads:
cwd = os.getcwd() # The Currently working directory - where this .py file can be found.

# Possible values for the laser Reputation.
rep_values_MHz = {'78.56MHz': 1, '39.28MHz': 2, '29.19MHz': 3, '19.64MHz': 4, '15.71MHz': 5, 
                '13.09MHz': 6, '11.22MHz': 7, '9.821MHz': 8, '8.729MHz': 9, '7.856MHz': 10, '6.547MHz': 12, 
                '5.612MHz': 14, '4.910MHz': 16, '4.365MHz': 18, '3.928MHz': 20, '3.571MHz': 22, '3.143MHz': 25, 
                '2.910MHz': 27, '2.709MHz': 29, '2.455MHz': 32, '2.311MHz': 34, '2.123MHz': 37, '1.964MHz': 40}

# The size of the GUI window (Width, Length).
SIZE = (600,630)

sg.theme('DefaultNoMoreNagging')
# sg.theme('DarkBlue')
# sg.theme('Default')

#---------------------------------------------------------------------------------------------------------------------------

# Functions:

# This function is the first Tab of the GUI window - Responsible for the connections with the Laser & OSA devices.
def getConnections():
    try:
        with open(cwd+"\\connections.json", 'r') as f:
            connectionsDict = load(f)
    except:
        data = {"OSA": {"IP": "10.0.0.101", "PORT": "10001"}, "LASER": {"COM": "COM6", "Serial": "15"}}
        with open("connections.json", "w") as write_file:
            dump(data, write_file)
        with open(cwd+"\\connections.json", 'r') as f:
            connectionsDict = load(f)
    connections = [[sg.Push(), sg.Text("OSA", font='David 15 bold'), sg.Push()],
                    [sg.Text("IP Address:"), sg.Push(), sg.Input(connectionsDict["OSA"]["IP"],s=15)],
                    [sg.Text("Port:"), sg.Push(), sg.Input(connectionsDict["OSA"]["PORT"],s=15)],
                    [sg.Push(), sg.Text("Laser", font='David 15 bold'), sg.Push()],
                    [sg.Text("COM:"), sg.Push(), sg.Input(connectionsDict["LASER"]["COM"],s=15)],
                    [sg.Text("Serial:"), sg.Push(), sg.Input(connectionsDict["LASER"]["Serial"],s=15)],
                    [sg.Push(), sg.Button("Connect"), sg.Push()],
                    [sg.Push(), sg.Text(getConnectionsText, key='getConnectText'), sg.Push()]]
    return connections

def updateConnections(values):
    # This function gets the values from the user in the main GUI window and if the connection was successful than it saves the correct parameters (IP Address, Port, COM, Serial) for the next connection.
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

#--- Here we finished with Connections.

#---------------------------------------------------------------------------------------------------------------------------

#--- Here we start with Layouts:

def collapse(layout, key, visible):
    # Hide or show the relevants fields. This function responsible for allowing us to show and hide relevant parts in a layout according to user checkbox chooses. When the relevant choice done there is an event, and this function is called to do the work.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

def getSampleL():
    # This function creates the layout for the second tab, the 'Single Sample' tab. This function allows to operate one single measurement and by that to learn each relevant parameter and his influence on the measurement result. To be prepared for the full test in the next tab.
    sampleL = [[sg.Push(), sg.Text("OSA", font='David 15 bold'), sg.Push()],
                [sg.Text("Center Wavelength:"), sg.Push(), sg.Input("1500",s=15,key="CF"), sg.Text("[nm]")],
                [sg.Text("Span:"), sg.Push(), sg.Input("50",s=15,key="SPAN"), sg.Text("[nm]")],
                [sg.Text("Number of Points (Auto recommended):"), sg.Push(), sg.Input("Auto",s=15,key="PTS")],
                [sg.Text("Sensetivity: "), sg.Push(), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="sens")],
                [sg.Text("Resolution: "), sg.Push(), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>"], enable_events=True, default_value="1nm <0.820nm>" ,key="res")],
                [sg.Text("")],
                [sg.Push(), sg.Text("Laser", font='David 15 bold'), sg.Push()],
                [sg.Text("Power:"), sg.Push(), sg.Input("6",s=15, key="POWER"), sg.Text("%")],
                [sg.Text("Repetition Rate:"), sg.Push(), sg.Combo(list(rep_values_MHz.keys()), key="REP", default_value=list(rep_values_MHz.keys())[0])],
                [sg.Text("")],
                [sg.Push(), sg.Text("Misc", font='David 15 bold'), sg.Push()],
                [sg.Checkbox("Save sample", key="Save"), sg.Push(), sg.Text("Output name:"), sg.Input("demo_sample", s=15, key="sample_name")],
                [sg.Checkbox("Plot sample", key="Plot")],
                [sg.Push(), sg.Button("Sample"), sg.Push()],
                [sg.Push(), sg.Text(getSamplesText, key="singleSampleText"), sg.Push()]]
    sample_message = [[sg.Push(), sg.Text("Connect to devices first or work in 'Debug Mode'"), sg.Push()]]
    sampleLayout = [[sg.Push(), collapse(sample_message, 'sample_status_message', True), sg.Push()], [sg.Push(), collapse(sampleL, 'sample_status_menu', False), sg.Push()]]
    return sampleLayout

def getTests():
    # This function creates the layout for the third tab, the 'Tests' tab. Here it is possible to set combinations of powers and repetitions, to choose the Laser and OSA parameters, to set the total time and interval time for Allan deviation and Beer-Lambert law.
    powerSweepSection = [[sg.Text("Stop Power Level"), sg.Input("50",s=3,key="maxPL"),sg.Text("Step:"), sg.Input("10",s=3,key="stepPL")]]
    analyzerSection = [[sg.Text("Total time for test"),sg.Input("60",s=3,key="totalSampleTime"),sg.Text("[seconds]"),sg.Push(),sg.Text("Interval time: "),sg.Input("1",
    s=3,key="intervalTime"), sg.Text("seconds")]]
    stopTestSection = [[sg.Button("Stop Test")]]
    test_values = [[sg.Push(), sg.Text("Tests - choose the tests you want", font='David 15 bold'), sg.Push()],
                [sg.Text("Center Wavelength:"), sg.Input("1500",s=5,key="test_CF"), sg.Text("[nm]"),
                sg.Text("Span:"), sg.Input("50",s=5,key="test_SPAN"), sg.Text("[nm]")],
                [sg.Text("Number of Points: (Auto recommended)"), sg.Input("Auto",s=12,key="test_PTS"), sg.Text("Sensetivity: "), sg.Combo(["NORM/HOLD", "NORM/AUTO", "NORMAL", "MID", "HIGH1", "HIGH2", "HIGH3"], default_value='MID',key="test_sens")], [sg.Text("Resolution: "), sg.Combo(["0.02nm <0.019nm>", "0.05nm <0.043nm>", "0.1nm <0.076nm>", "0.2nm <0.160nm>", "0.5nm <0.408nm>", "1nm <0.820nm>", "2nm <1.643nm>"], enable_events=True, default_value="1nm <0.820nm>" ,key="test_res")],
                [sg.Text("Start Power Level [%]:"), sg.Input("6",s=3,key="minPL"), sg.Checkbox(text="Sweep?", enable_events=True, key="testPowerLevelSweep"), collapse(powerSweepSection, 'section_powerSweep', False)],
                [sg.Text("Sample Averaging (Dark Measurments): "), sg.Input("5",s=2,key="darkNumSamplesParameter"), sg.Text("(max: 100)")],
                [sg.Text("Sample Averaging (Clean/Empty Measurments): "), sg.Input("5",s=2,key="cleanNumSamplesParameter"), sg.Text("(max: 100)")],
                [sg.Text("Sample Averaging (Substance): "), sg.Input("1",s=2,key="substanceNumSamplesParameter"), sg.Text("(max: 100)")],
                [sg.Text("Choose the repetition rates [MHz]:"),sg.Checkbox(text="Select all", enable_events=True, key="selectAllRep")],
                [sg.Checkbox(text="78.56",font='David 11',key="r1",default=False),sg.Checkbox(text="39.28",font='David 11',key="r2",default=False),sg.Checkbox(text="29.19",font='David 11',key="r3",default=False),sg.Checkbox(text="19.64",font='David 11',key="r4",default=False),sg.Checkbox(text="15.71",font='David 11',key="r5",default=False),sg.Checkbox(text="13.09",font='David 11',key="r6",default=False),sg.Checkbox(text="11.22",font='David 11',key="r7",default=False),sg.Checkbox(text="9.82",font='David 11',key="r8",default=False)],
                [sg.Checkbox(text="8.729",font='David 11',key="r9",default=False),sg.Checkbox(text="7.856",font='David 11',key="r10",default=False),sg.Checkbox(text="6.547",font='David 11',key="r12",default=False),sg.Checkbox(text="5.612",font='David 11',key="r14",default=False),sg.Checkbox(text="4.910",font='David 11',key="r16",default=False),sg.Checkbox(text="4.365",font='David 11',key="r18",default=False),sg.Checkbox(text="3.928",font='David 11',key="r20",default=False),sg.Checkbox(text="3.571",font='David 11',key="r22",default=False)],
                [sg.Checkbox(text="3.143",font='David 11',key="r25",default=False),sg.Checkbox(text="2.910",font='David 11',key="r27",default=False),sg.Checkbox(text="2.709",font='David 11',key="r29",default=False),sg.Checkbox(text="2.455",font='David 11',key="r32",default=False),sg.Checkbox(text="2.311",font='David 11',key="r34",default=False),sg.Checkbox(text="2.123",font='David 11',key="r37",default=False),sg.Checkbox(text="1.964",font='David 11',key="r40",default=False)],
                [],[],
                [sg.Text("Output name:"), sg.Input("Test_sample1", s=15, key="test_name"), sg.Push(), sg.Text("Comments:"),sg.Input("",s=30,key="TEST1_COMMENT")], [],
                [sg.Checkbox(text="Analyzer (Beer-Lambert & Allan Deviation) ?",enable_events=True,key="test_analyzer")], [collapse(analyzerSection, 'section_analyzer', False)],
                [sg.Push(), sg.Button("Start Test"), sg.Push()],[sg.Push(), collapse(stopTestSection, 'section_stopTest', False), sg.Push()],
                [sg.Push(),sg.Text(str(getTestErrorText), key="test_errorText", justification='center'),sg.Push()]]
    test_message = [[sg.Push(), sg.Text("Connect to devices first or run in 'Debug Mode'"), sg.Push()]]
    #
    test_values = [[sg.Push(), collapse(test_message, 'test_status_message', True), sg.Push()], [sg.Push(), collapse(test_values, 'test_status_menu', False), sg.Push()]]
    return test_values

def getDatabases():
    # This function checks and show the list of files that are possible to load for the 'Results' tab.
    try:
        foldersNames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        foldersNames = os.listdir("..\\Databases")
    foldersNames.sort()   
    return foldersNames

# The fourth layout - the results window:
def getResultsTabLayout():
    # This function creates the layout for the fourth tab, the 'Results' tab. This tab allows to load, show, and compare on the graphs previous measurements were done.
    try:
        foldersNames = os.listdir("..\\Results")
    except:
        os.mkdir("..\\Results")
        foldersNames = os.listdir("..\\Results")
    foldersNames.sort()
    Layout = [[sg.Text("Select sample to plot", font='David 15 bold')],
                [sg.Listbox(foldersNames, select_mode='LISTBOX_SELECT_MODE_SINGLE', key="-SAMPLE_TO_PLOT-", size=(SIZE[1],20))],
                [sg.Push(), sg.Button("Load", key="-LOAD_SAMPLE-"), sg.Button("Delete", key="-DELETE_SAMPLE-"), sg.Push()]]
    return Layout

def getCalibrationTabLayout():
    Layout = [[sg.Push(), sg.Text("Calibration Process", font='David 20 bold'), sg.Push()],
              [sg.Push(), sg.Button("Start calibration", key="-START_CAL-"), sg.Push()],
              [sg.Push(), sg.Button("Stop calibration", key="-STOP_CAL-"), sg.Push()],
              # [sg.Listbox(foldersNames, select_mode='LISTBOX_SELECT_MODE_SINGLE', key="-SAMPLE_TO_PLOT-",
              #             size=(SIZE[1], 20))],
              [sg.Push(),sg.Multiline(size=(80, 20), key="-CAL_PRINTS-", autoscroll=True, disabled=True),sg.Push()]]
    return Layout

def updateResults(window):
    # This function is to update the list in the 'Results' tab after a measurement was finished.
    foldersNames = os.listdir("..\\Results")
    foldersNames.sort()
    window['-SAMPLE_TO_PLOT-'].update(foldersNames)

# End of Layouts.

#---------------------------------------------------------------------------------------------------------------------------

# Relevant functions for the GUI:

def open_Interactive_Graphs(dirName, analyzer_substance = False):
    args = [dirName]
    process = Process(target=interactiveGraph, args=args)
    process.start()
    if process != False:
        return process.pid # return the process number.
    else:
        return False


def open_calibration_process(output_queue):
    process = Process(target=start_CAl_main, args=(output_queue,))
    process.start()
    if process != False:
        return process.pid # return the process number.
    else:
        return False

def STOP_calibration_process():
    process = Process(target=start_CAl_main)
    process.start()
    if process != False:
        return process.pid # return the process number.
    else:
        return False



def updateJsonFileOfTestsParameters(values):
    # This funciton save the tests parameters from GUI that setup by the user.
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    # Parameters:
    connectionsDict["Samples"]["CF"] = values['CF']
    connectionsDict["Samples"]["Span"] = values['SPAN']
    connectionsDict["Samples"]["Points"] = values['PTS']
    connectionsDict["Samples"]["Sens"] = values['sens']
    connectionsDict["Samples"]["Res"] = values['res']
    connectionsDict["Samples"]["Power"] = values['POWER']
    connectionsDict["Samples"]["Rep"] = values['REP']
    connectionsDict["Samples"]["SaveSample"] = values['Save']
    connectionsDict["Samples"]["Plot"] = values['Plot']
    connectionsDict["Samples"]["OutputName"] = values['sample_name']
    connectionsDict["Tests"]["CF"] = values['test_CF']
    connectionsDict["Tests"]["Span"] = values['test_SPAN']
    connectionsDict["Tests"]["Points"] = values['test_PTS']
    connectionsDict["Tests"]["Sens"] = values['test_sens']
    connectionsDict["Tests"]["Res"] = values['test_res']
    connectionsDict["Tests"]["StartPower"] = values['minPL']
    connectionsDict["Tests"]["Sweep"] = values['testPowerLevelSweep']
    connectionsDict["Tests"]["EndPower"] = values['maxPL']
    connectionsDict["Tests"]["Step"] = values['stepPL']
    connectionsDict["Tests"]["AvgDark"] = values['darkNumSamplesParameter']
    connectionsDict["Tests"]["AvgClean"] = values['cleanNumSamplesParameter']
    connectionsDict["Tests"]["AvgSubstance"] = values['substanceNumSamplesParameter']
    connectionsDict["Tests"]["SelectAll"] = values['selectAllRep']
    connectionsDict["Tests"]["78.56"] = values['r1']
    connectionsDict["Tests"]["39.28"] = values['r2']
    connectionsDict["Tests"]["29.19"] = values['r3']
    connectionsDict["Tests"]["19.64"] = values['r4']
    connectionsDict["Tests"]["15.71"] = values['r5']
    connectionsDict["Tests"]["13.09"] = values['r6']
    connectionsDict["Tests"]["11.22"] = values['r7']
    connectionsDict["Tests"]["9.82"] = values['r8']
    connectionsDict["Tests"]["8.729"] = values['r9']
    connectionsDict["Tests"]["7.856"] = values['r10']
    connectionsDict["Tests"]["6.547"] = values['r12']
    connectionsDict["Tests"]["5.612"] = values['r14']
    connectionsDict["Tests"]["4.910"] = values['r16']
    connectionsDict["Tests"]["4.365"] = values['r18']
    connectionsDict["Tests"]["3.928"] = values['r20']
    connectionsDict["Tests"]["3.571"] = values['r22']
    connectionsDict["Tests"]["3.143"] = values['r25']
    connectionsDict["Tests"]["2.910"] = values['r27']
    connectionsDict["Tests"]["2.709"] = values['r29']
    connectionsDict["Tests"]["2.455"] = values['r32']
    connectionsDict["Tests"]["2.311"] = values['r34']
    connectionsDict["Tests"]["2.123"] = values['r37']
    connectionsDict["Tests"]["1.964"] = values['r40']
    connectionsDict["Tests"]["OutputName"] = values['test_name']
    connectionsDict["Tests"]["Comments"] = values['TEST1_COMMENT']
    connectionsDict["Tests"]["Analyzer"] = values['test_analyzer']
    connectionsDict["Tests"]["TotalTime"] = values['totalSampleTime']
    connectionsDict["Tests"]["IntervalTime"] = values['intervalTime']
    #
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

def updateJsonFileBeforeEnd(values):
    # This funciton save default connection parameters.
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    connectionsDict["OSA"]["IP"] = values[0]
    connectionsDict["OSA"]["PORT"] = values[1]
    connectionsDict["LASER"]["COM"] = values[2]
    connectionsDict["LASER"]["Serial"] = values[3]
    connectionsDict["Samples"]["Serial"] = values[3]
    with open(cwd+"\\connections.json", 'w') as f:
        dump(connectionsDict, f)

def reloadParameters(window):
    with open(cwd+"\\connections.json", 'r') as f:
        connectionsDict = load(f)
    # Loading from Json file to the window:
    window['CF'].update(connectionsDict["Samples"]["CF"])
    window['SPAN'].update(connectionsDict["Samples"]["Span"])
    window['PTS'].update(connectionsDict["Samples"]["Points"])
    window['sens'].update(connectionsDict["Samples"]["Sens"])
    window['res'].update(connectionsDict["Samples"]["Res"])
    window['POWER'].update(connectionsDict["Samples"]["Power"])
    window['REP'].update(connectionsDict["Samples"]["Rep"])
    window['Save'].update(connectionsDict["Samples"]["SaveSample"])
    window['Plot'].update(connectionsDict["Samples"]["Plot"])
    window['sample_name'].update(connectionsDict["Samples"]["OutputName"])
    window['test_CF'].update(connectionsDict["Tests"]["CF"])
    window['test_SPAN'].update(connectionsDict["Tests"]["Span"])
    window['test_PTS'].update(connectionsDict["Tests"]["Points"])
    window['test_sens'].update(connectionsDict["Tests"]["Sens"])
    window['test_res'].update(connectionsDict["Tests"]["Res"])
    window['minPL'].update(connectionsDict["Tests"]["StartPower"])
    window['testPowerLevelSweep'].update(connectionsDict["Tests"]["Sweep"])
    window['maxPL'].update(connectionsDict["Tests"]["EndPower"])
    window['stepPL'].update(connectionsDict["Tests"]["Step"])
    window['darkNumSamplesParameter'].update(connectionsDict["Tests"]["AvgDark"])
    window['cleanNumSamplesParameter'].update(connectionsDict["Tests"]["AvgClean"])
    window['substanceNumSamplesParameter'].update(connectionsDict["Tests"]["AvgSubstance"])
    window['selectAllRep'].update(connectionsDict["Tests"]["SelectAll"])
    window['r1'].update(connectionsDict["Tests"]["78.56"])
    window['r2'].update(connectionsDict["Tests"]["39.28"])
    window['r3'].update(connectionsDict["Tests"]["29.19"])
    window['r4'].update(connectionsDict["Tests"]["19.64"])
    window['r5'].update(connectionsDict["Tests"]["15.71"])
    window['r6'].update(connectionsDict["Tests"]["13.09"])
    window['r7'].update(connectionsDict["Tests"]["11.22"])
    window['r8'].update(connectionsDict["Tests"]["9.82"])
    window['r9'].update(connectionsDict["Tests"]["8.729"])
    window['r10'].update(connectionsDict["Tests"]["7.856"])
    window['r12'].update(connectionsDict["Tests"]["6.547"])
    window['r14'].update(connectionsDict["Tests"]["5.612"])
    window['r16'].update(connectionsDict["Tests"]["4.910"])
    window['r18'].update(connectionsDict["Tests"]["4.365"])
    window['r20'].update(connectionsDict["Tests"]["3.928"])
    window['r22'].update(connectionsDict["Tests"]["3.571"])
    window['r25'].update(connectionsDict["Tests"]["3.143"])
    window['r27'].update(connectionsDict["Tests"]["2.910"])
    window['r29'].update(connectionsDict["Tests"]["2.709"])
    window['r32'].update(connectionsDict["Tests"]["2.455"])
    window['r34'].update(connectionsDict["Tests"]["2.311"])
    window['r37'].update(connectionsDict["Tests"]["2.123"])
    window['r40'].update(connectionsDict["Tests"]["1.964"])
    window['test_name'].update(connectionsDict["Tests"]["OutputName"])
    window['TEST1_COMMENT'].update(connectionsDict["Tests"]["Comments"])
    window['test_analyzer'].update(connectionsDict["Tests"]["Analyzer"])
    window['totalSampleTime'].update(connectionsDict["Tests"]["TotalTime"])
    window['intervalTime'].update(connectionsDict["Tests"]["IntervalTime"])
    if connectionsDict["Tests"]["Sweep"] == True:
        window['section_powerSweep'].update(visible=True)
    if connectionsDict["Tests"]["Analyzer"] == True:
        window['section_analyzer'].update(visible=True)
    #
    return window

def checkStartConditions(values):
    # Checking all the condition if everything is ok and we can start the test:
    getTestErrorText = ""
    if (int(values["test_CF"]) < 700):
        getTestErrorText = "Error: The 'Center Wavelength' can only be between 700nm to 1600nm."
    elif (int(values["test_SPAN"]) > 250):
        getTestErrorText = "Error: The 'Span' value can only be between XXX to YYY."
    elif (values["test_PTS"] != "Auto"):
        try:
            if (int(values["test_PTS"]) > 2000) or (int(values["test_PTS"]) < 101):
                getTestErrorText = "Error: The max Number of Points per sample is should be between 101 to 2,000 points."
        except:
                getTestErrorText = "Error: The max Number of Points per sample should be an int! between 101 to 2,000 points."
    elif ( (values["test_res"] == "Manuall (Enter a value)") and ((float(values["test_manuallRes"]) < 0) or (float(values["test_manuallRes"]) > 4) )):
        getTestErrorText = "Error: The resolution you enter is not good value."
    elif (int(values["minPL"]) < 6 or int(values["minPL"]) > 100):
        getTestErrorText = "Error: The start power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["maxPL"]) < 6 or int(values["maxPL"]) > 100) ):
        getTestErrorText = "Error: The end power of the laser must be btween 6 to 100"
    elif ( values["testPowerLevelSweep"] and (int(values["minPL"]) > int(values["maxPL"])) ):
        getTestErrorText = "Error: The start power must be smaller than the end power"
    elif int(values["darkNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Dark) must be higher than 0"
    elif int(values["cleanNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Clean) must be higher than 0"
    elif int(values["substanceNumSamplesParameter"]) <= 0:
        getTestErrorText = "Error: The number of samples (Substannce) must be higher than 0"
    elif (not values["r1"] and not values["r2"] and not values["r3"] and not values["r4"] and not values["r5"] and not values["r6"] and not values["r7"] and not values["r8"] and not values["r9"] and not values["r10"] and not values["r12"] and not values["r14"] and not values["r16"] and not values["r18"] and not values["r20"] and not values["r22"] and not values["r25"] and not values["r27"] and not values["r29"] and not values["r32"] and not values["r34"] and not values["r37"] and not values["r40"]):
        getTestErrorText = "Error: No repetition value was chosen"
    elif (values["test_name"] == ""): # Not a must.
        getTestErrorText = "Error: No name for 'Output name'."
    elif (values["test_analyzer"] and ( (int(values["totalSampleTime"]) < 0) or (int(values["totalSampleTime"]) > 3600) )):
        getTestErrorText = "Error: (Analyzer) The 'Total time sample' must be bigger than zero. Max: 1 Hour."
    elif (values["test_analyzer"] and ( (float(values["intervalTime"]) < 0.1) or (float(values["intervalTime"]) > int(values["totalSampleTime"])) )):
        getTestErrorText = "Error: (Analyzer) The interval time must be bigger than 0.5 seconds and smaller from the Total time."
    return getTestErrorText

#---------------------------------------------------------------------------------------------------------------------------

def reopenMainL(window = None):
    # This function start the GUI window:
    mainL = [[sg.TabGroup([[sg.Tab('Connections',getConnections(), key='-TAB1-'), sg.Tab('Single Sample', getSampleL(), key='-TAB2-'), sg.Tab('Tests', getTests(), key='-TAB3-'), sg.Tab('Results', getResultsTabLayout(), key='-TAB4-'), sg.Tab('Calibration', getCalibrationTabLayout(), key='-TAB5-')]], key='-TABGROUP-', size = (SIZE[0]+30,SIZE[1]-70))],[sg.Button("Close"), sg.Button("Debug Mode"), sg.Push(), sg.Text(status, key='status')]]
    try:
        window.close()
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE, finalize = True)
    except:
        window = sg.Window('Lab Tool', mainL, disable_close=True, size = SIZE, finalize = True)
    return window

def popup(message):
    # This function gets a message and create a popup window with this message.
    # sg.theme('DarkGrey')
    # sg.theme('Default')
    sg.theme('DefaultNoMoreNagging')
    layout = [[sg.Text(message)]]
    window = sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window

#----------------------------------------------------------------------------------------------------------------------------------------

class theTestThread(threading.Thread):
    def __init__(self, arg1, arg2, arg3, arg4, arg5, arg6):
        # This is the first, default and must function of the class. Setup all the relevant objects and parameters the class will use to call the relevant functions for the test from the thread.
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.arg1 = arg1 # Laser
        self.arg2 = arg2 # OSA
        self.arg3 = arg3 # values
        self.arg4 = arg4 # debugMode
        self.arg5 = arg5 # dirName
        self.arg6 = arg6 # window
        self.result = None

    def run(self):
        # This is the function that manage all the test process & operation. It allows the threading and parallel operation to the main GUI, or an open Interactive Graph.
        # Set names:
        laser = self.arg1
        osa = self.arg2
        values = self.arg3
        debugMode = self.arg4
        dirName = self.arg5
        window = self.arg6
        reason = None
        #
        window['test_errorText'].update("Part 1/3: Executing 'Dark' Test...")
        noiseMeasurments(laser, osa ,values, debugMode, dirName+"\\dark.csv")
        try:
            window['test_errorText'].update("Part 2/3: Executing 'Clean/Empty' Tests...")
        except:
            return False
        reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\clean.csv", window, "Part 2/3: Executing 'Clean/Empty' Tests...", self)
        if reason == False:
            self.result = False
            if isConnected:
                laser.emission(0)
            # del laser
            # del self.arg1
            return False
        window['test_errorText'].update("Part 2/3: Executing 'Clean/Empty' Tests... (100%)")
        # For user:
        tempEvent = tkm.askokcancel(title="Enter Substance!", message="Empty measurment finished.\nPlease insert substance, then press 'OK'.\nChoosing 'Cancel' will stop the all process\nand delete all the measurments.")
        #tempEvent = sg.popup_ok_cancel("Enter Substance!", "Empty measurment finished.\nPlease insert substance, then press 'OK'.\nChoosing 'Cancel' will stop the all process\nand delete all the measurments.")
        # OK was chosen:
        if tempEvent:
            window['test_errorText'].update("Part 3/3: Executing 'Substance' Test...")
            if (values['test_analyzer']):
                if (not debugMode):
                    laser.emission(0)
                    sleep(8)
                reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\analyzer.csv", window, "Part 3/3: Executing 'Substance' Tests...", self) 
            else:
                reason = getSweepResults(laser,osa,values,debugMode,dirName+"\\substance.csv", window, "Part 3/3: Executing 'Substance' Tests...", self)
            if reason == False:
                self.result = False
                if isConnected:
                    laser.emission(0)
                # del laser
                # del self.arg1
                return False
            window['test_errorText'].update("Part 3/3: Executing 'Substance' Test... (100%)")
            # Adding to Results tab.
            updateResults(window)
            # Open a new process of the graph/grphs.
            if reason != False: # Everyting is OK, can open Graphs window.
                processPID = open_Interactive_Graphs(dirName + "\\") # process ID or False
                if processPID != False:
                    graphs_pids.append(processPID)
                    window['test_errorText'].update("Finish Testing.")
                else:
                    window['test_errorText'].update("There was some problem! Probably because missing files.")
        else:
            shutil.rmtree(dirName)
        window['Sample'].update(disabled=False)
        window['Start Test'].update(disabled=False)
        window['section_stopTest'].update(visible=False)
        if reason:
            self.result = True
            if isConnected:
                laser.emission(0)
            # del laser
            # del self.arg1
            return True
    # End of the test thread.

    def stop(self):
        # This function allows the stop of the running thread.
        self.stop_event.set()

#----------------------------------------------------------------------------------------------------------------------------------------

# The next funcion 'main' is to ensure the GUI.py file will not creates copy of himself every time we are creating a process by the multiprocessing library.
def main(mode = 0):
    cal_proceess_pid = None
    isConnected = False
    window = reopenMainL()
    output_queue = Queue()


    if (mode != 0 ):
        # Here we are doing reconnect to the device and after that loading the test parameters again:
        window['-TAB3-'].select()
        window = reloadParameters(window) # Updating all the other parameters.
        if (mode == 1):
            event, values = window.read()
            # Try to connect.
            try:
                osa = OSA(values[0])
                laser = Laser(values[2])
                if not isConnected:
                    isConnected = True
                    debugMode = False
                    status = "Devices are connected"
                    getConnectionsText = getSamplesText = getTestErrorText = "The devices are connected"
                    window['sample_status_message'].update(visible=False)
                    window['sample_status_menu'].update(visible=True)
                    window['test_status_message'].update(visible=False)
                    window['test_status_menu'].update(visible=True)
                    window['status'].update(status)
                    window['getConnectText'].update(getConnectionsText)
                    window['getConnectText'].update("Connection successful! You are now connected to the devices")
                    window['test_errorText'].update("The testing process was stopped.")
            except:
                window['getConnectText'].update("Failed to connect to OSA or Laser, try again or continue wiht 'Debug mode'.")
                print("Failed to connect to OSA or Laser, try again or continue wiht 'Debug mode'.")
        if (mode == 2):
            debugMode = True
            status = "Debug Mode"
            getConnectionsText = getSamplesText = getTestErrorText = "Now you are working in 'Debug Mode'!"
            laser = None
            osa = None
            window['sample_status_message'].update(visible=False)
            window['sample_status_menu'].update(visible=True)
            window['test_status_message'].update(visible=False)
            window['test_status_menu'].update(visible=True)
            window['status'].update(status)
            window['getConnectText'].update(getConnectionsText)
            window['test_errorText'].update("The testing process was stopped.")
    # End of Setup

    while True:

        event, values = window.read(timeout=100)
        #queue handler - read from main_calibration queue and print or pop-up message accordingly
        while not output_queue.empty():
            message = output_queue.get()
            if message == "TERMINATE_bad_Spot":
                sg.popup("The system detected a suspected light spot, but it's not large enough.\nThe system wll move to position of suspected spot, please calibrate the system on the right side to ensure a clear spot is visible in the camera, with a recommended exposure of 0.001", title="Alert: suspected light spot detected")
                event == "-STOP_CAL-"
            if message == "TERMINATE_nothing":
                sg.popup("The system was unable to detect a line.\nPlease recalibrate the system on the left side to ensure a clear line is visible in the camera", title="Alert: Line detection failed")
                event == "-STOP_CAL-"
            if message == "TERMINATE_spot":
                sg.popup("The system was unable to detect a light spot.\nThe system will move to suspected spot location, please calibrate the system on the right side to ensure a clear spot is visible in the camera", title="Alert: Spot detection failed")
                event == "-STOP_CAL-"
            elif message == "TERMINATE":
                sg.popup("Pop up for user - recalibrate please", title="IMPORTANT")
                event =="-STOP_CAL-"
            else:
                window["-CAL_PRINTS-"].update(message, append=True)



        if event == 'Connect':
            # Try connect the devices:
            try:
                osa = OSA(values[0])
                laser = Laser(values[2])
                if not isConnected:
                    isConnected = True
                    debugMode = False
                    status = "Devices are connected"
                    getConnectionsText = getSamplesText = getTestErrorText = "The devices are connected"
                    window['sample_status_message'].update(visible=False)
                    window['sample_status_menu'].update(visible=True)
                    window['test_status_message'].update(visible=False)
                    window['test_status_menu'].update(visible=True)
                    window['status'].update(status)
                    window['getConnectText'].update(getConnectionsText)
                    window['getConnectText'].update("Connection successful! You are now connected to the devices")
            except:
                window['getConnectText'].update("Failed to connect to OSA or Laser, try again or continue wiht 'Debug mode'.")
                print("Failed to connect to OSA or Laser, try again or continue wiht 'Debug mode'.")
            updateConnections(values)
            
        elif event == 'Debug Mode':
            # Move and working in Debug Mode to allow the relevant functions and rest of the GUI.
            debugMode = True
            status = "Debug Mode"
            getConnectionsText = getSamplesText = getTestErrorText = "Now you are working in 'Debug Mode'!"
            laser = None
            osa = None
            window['sample_status_message'].update(visible=False)
            window['sample_status_menu'].update(visible=True)
            window['test_status_message'].update(visible=False)
            window['test_status_menu'].update(visible=True)
            window['status'].update(status)
            window['getConnectText'].update(getConnectionsText)

        elif event == 'Sample':
            # To do only one sample.
            # Checking for correct settings:
            getSamplesText = ""
            if (values["PTS"] != "Auto"):
                try:
                    if (int(values["PTS"]) > 2000) or (int(values["PTS"]) < 101):
                        getSamplesText = "Error: The max Number of Points per sample is XXX points."
                except:
                    getSamplesText = "Error: The number of Points per sample should be between 101 to 2,000 points."
            if ( (int(values["POWER"]) < 6 or int(values["POWER"]) > 100) ):
                getSamplesText = "Error: The power of the laser must be btween 6 to 100"
            #
            if debugMode:
                getSamplesText = "Everything is OK, the sample finished successfully"
            if ( ( isConnected or (not debugMode) ) and getSamplesText == "" ):
                setConfig(laser,osa,values["CF"],values["SPAN"],values["PTS"],values["POWER"],values["REP"],values["sens"],values["res"])
                getSamplesText = runSample(laser,osa, isConnected,debugMode, values)
        
        elif event == "testPowerLevelSweep":
            # To show the power test parameters setting–the line will continue in the GUI.
            if (values["testPowerLevelSweep"] == True):
                window['section_powerSweep'].update(visible=True)
            else:
                window['section_powerSweep'].update(visible=False)

        elif event == "selectAllRep":
            # Checking or unchecking all the reputations together.
            RepList = ["r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r12","r14","r16","r18","r20","r22","r25","r27","r29","r32","r34","r37","r40"]
            for i in RepList:
                values[i] = values['selectAllRep']
                window[i].update(values["selectAllRep"])
            print(values)

        elif event == "test_analyzer":
            # To show the parameters part of the analyzer setting.
            if (values["test_analyzer"] == True):
                window['section_analyzer'].update(visible=True)
            else:
                window['section_analyzer'].update(visible=False)

        elif event == "Start Test":
            # Start a full test with the parameters that set up from the user in the 'Tests' tab. First there is a need to cheek if all the parameters are OK.
            if (isConnected or debugMode):
                getTestErrorText = checkStartConditions(values) # Checking if all the parameters & conditions to start the tests are OK.
                if (getTestErrorText == ""):
                    # EveryThing is OK - Starting the test.
                    if values["test_res"] == "Manuall (Enter a value)":
                        res = values["test_manuallRes"]
                    else:
                        res = values["test_res"]
                    updateJsonFileOfTestsParameters(values)
                    window['Sample'].update(disabled=True)
                    window['Start Test'].update(disabled=True)
                    window['section_stopTest'].update(visible=True)
                    window['test_errorText'].update("Executing Clean Test...")
                    dirName = makedirectory(values["test_name"],values["test_CF"],values["test_SPAN"],values["test_PTS"],values["test_sens"],res,values["test_analyzer"])
                    testThread = theTestThread(laser,osa,values,debugMode,dirName,window)
                    testThread.start()
                else:
                    window['test_errorText'].update(getTestErrorText)
                getTestErrorText = ""

        elif event == "Stop Test":
            # This function support to stop the test. The maximum wait time until stop is the 'Interval time' that set or available/possible (The longer).
            tempEvent = sg.popup_ok_cancel("Stop Running test?", "Are you sure you want to stop the running test?\n'Ok' - Yes, stop the test.\n'Cancel' - Opps, continue the test.")
            if (tempEvent.upper()=="OK"):
                # Open and close a window
                testThread.stop()
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                animation = time.time()
                timeToWaitForStop = time.time()
                while ( (testThread.result != False) and (time.time() - timeToWaitForStop <= 2*float(values['intervalTime'])) ):
                    if (time.time() - animation > 0.05):
                        sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                        animation = time.time()
                sg.PopupAnimated(None)
                if isConnected:
                    laser.emission(0)
                # del laser
                # os.kill(testThread.ident, signal.SIGTERM) # I added
                del testThread
                window['section_stopTest'].update(visible=False)
                window['Sample'].update(disabled=False)
                window['Start Test'].update(disabled=False)
                window['test_errorText'].update("The testing process was stopped.")
                sg.popup_ok("The test process was stopped by the user!\nPress 'Ok' and please wait.")
                updateJsonFileBeforeEnd(values)
                updateJsonFileOfTestsParameters(values)
                # Now we will close the specific main GUI process that running:
                window.close()
                # Save the test results to json file.
                getTestErrorText = ""
                # Now we can get out of the main function to kill the process and running thread after stopping it and we will open a new process after we return value.
                # We just need to relaunch the main GUI window: 2 - 'Debug Mode', 1 - 'Connect again'
                if debugMode:
                    return 2
                else:
                    return 1

        elif event == "-LOAD_SAMPLE-":
            # This function loads a result from the fourth tab.
            dirName = "..\\Results\\"+values['-SAMPLE_TO_PLOT-'][0]+"\\"
            processPID = open_Interactive_Graphs(dirName)
            if processPID != False:
                graphs_pids.append(processPID)
            else:
                tkm.showerror(title="Problem in loading the file", message="There was a problem in loading this measurment, probably because missing files.")

        elif event =="-START_CAL-":
            window["-CAL_PRINTS-"].update("Calibration STARTED.\n", append=True)
            processPID = open_calibration_process(output_queue)
            # while not output_queue.empty():
            #     message = output_queue.get()
            #     window["-CAL_PRINTS-"].update(message, append=True)
            if processPID != False:
                graphs_pids.append(processPID)
                cal_proceess_pid = processPID
            else:
                tkm.showerror(title="Problem in loading the file",
                              message="There was a problem in loading this measurment, probably because missing files.")

        elif event =="-STOP_CAL-":
            if cal_proceess_pid is not None:
                try:
                    os.system(f'taskkill /F /PID {cal_proceess_pid}')
                    # os.kill(pid, signal.SIGTERM)
                    print(f"Process with PID {cal_proceess_pid} killed successfully.")
                except OSError as e:
                    print(f"Error killing process with PID {cal_proceess_pid}: {e}")
            else:
                print("You probably didn't start the calibration")
            window["-CAL_PRINTS-"].update("Calibration STOPPED.\n", append=True)

            # try:
            #     # Check if the process with the given PID exists
            #     process = psutil.Process(cal_proceess_pid)
            #     # Terminate the process
            #     process.terminate()
            #     process.wait(timeout=3)  # Wait for the process to terminate
            #     print(f"Process with PID {cal_proceess_pid} killed successfully.")
            # except psutil.NoSuchProcess:
            #     print(f"No process found with PID {cal_proceess_pid}. You probably didn't start the calibration.")
            # except psutil.TimeoutExpired:
            #     print(f"Process with PID {cal_proceess_pid} did not terminate in time.")
            # except Exception as e:
            #     print(f"Error killing process with PID {cal_proceess_pid}: {e}")




        elif event == '-DELETE_SAMPLE-':
            # This function deletes the selected result from the results list in the fourth tab.
            tempEvent = sg.popup_ok_cancel("Are you sure you  want to delete this sample?")
            if ( tempEvent.upper() == "OK" ):
                try:
                    dirName = "..\\Results\\"+values['-SAMPLE_TO_PLOT-'][0]+"\\"
                    shutil.rmtree(dirName)
                except:
                    continue
                updateResults(window)
                #window['-SAMPLE_TO_PLOT-'].Update()

        elif ( (event == 'Close') or (event == sg.WIN_CLOSED) ):
            # This function close the main GUI.
            window.close()
            for pid in graphs_pids:
                try:
                    os.system(f'taskkill /F /PID {pid}')
                    # os.kill(pid, signal.SIGTERM)
                    print(f"Process with PID {pid} killed successfully.")
                except OSError as e:
                    print(f"Error killing process with PID {pid}: {e}")
            return 0
            # break
# End of main function.

# -----

def install_packages_message(val):
    if val == False:
        import tkinter.messagebox as tkm # tkinter is in the standard Pyhon library.
        tkm.showinfo("Message", "Installing/Updating relevant packages! Press 'OK'and please wait.")
    return True

def install_packages():
    # This function checks if all the relevants packages are installed on the PC.
    # The python standard library: https://docs.python.org/3/library/
    import sys # sys is the standard Python library.
    import subprocess # subprocess is the standard Python library.
    import tkinter.messagebox as tkm # tkinter is in the standard Pyhon library.
    val = False # No message already printed.
    # json is in the standard Python library.
    # time is the standard Python library.
    # multiprocessing is in the standard Pyhon library.
    # os is in the standard Pyhon library.
    # shutil is in the standard Pyhon library.
    # threading is in the standard Pyhon library.
    # datetime is in the standard Pyhon library.
    # argparse is in the standard Pyhon library.
    # concurrent.futures is in the standard Python library.
    #
    # ------------------------------
    # import PySimpleGUI library:
    try:
        import PySimpleGUI as sg
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'PySimpleGUI'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PySimpleGUI'])
        import PySimpleGUI as sg
    # ------------------------------
    # import pandas library:
    try:
        import pandas as pd
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pandas'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
        import pandas as pd
    # ------------------------------
    # import numpy library:
    try:
        import numpy as np
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'numpy'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
        import numpy as np
    # ------------------------------
    # import matplotlib library:
    try:
        import matplotlib.pyplot as plt
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'matplotlib'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'matplotlib'])
        import matplotlib.pyplot as plt
    # ------------------------------
    # import allantools library:
    try:
        import allantools
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'allantools'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'allantools'])
        import allantools
    # ------------------------------
    # import scipy.signal library:
    try:
        from scipy.signal import butter, cheby1, filtfilt
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'scipy'])
        except:
            None
    except:
        val = install_packages_message(val)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'scipy'])
        from scipy.signal import butter, cheby1, filtfilt
    # ------------------------------
# End of install_packages function.

if __name__ == '__main__':
# The checking events - The managment of the GUI:
    # install_packages() # This is good for installing & updating the relevant libraries.
    freeze_support()
    # main()
    # val == 0: End of Program,
    # val == 1: Connecting Mode,
    # val == 2: Debug Mode.
    val = main()
    while (val != 0): # The test was stopped - reload again the main GUI window:
        val = main(val)
    # The program finished - Need to close all the windows:
    print("The program is finished. Thank you & Goodbye.")

# End of 'GUI.py' file.
