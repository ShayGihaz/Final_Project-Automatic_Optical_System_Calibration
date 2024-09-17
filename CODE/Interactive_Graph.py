# This file is responsible for the results GUI, it contains the layouts for the Graphs. In addition, it contains all the relevant functions to control, operate and show of these graphs.
import argparse
import os
import time
from Analyzer import get_clean_substance_transmittance, beerLambert, allandevation
from datetime import datetime
from multiprocessing import Process, freeze_support
import pandas as pd
import PySimpleGUI as sg
import time
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors
import tkinter.messagebox as tkm
import matplotlib.collections as clt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Parameters:
#SIZE = (WIDTH,LENTH/HIGH):
MEKADEM = 1 # The Ratio of all.
WINDOW_SIZE = (int(1920*MEKADEM),int(1080*MEKADEM)) # The all window size.
FRAME_SIZE = (0.77*WINDOW_SIZE[0]+100,0.7*WINDOW_SIZE[1]+110) # The white box of the frame.
SETTING_AREA_SIZE = (0.18*WINDOW_SIZE[0],0.61*WINDOW_SIZE[1]) # All the data in the frame.
GRAPH_SIZE_AREA = (0.8*WINDOW_SIZE[0], 0.8*WINDOW_SIZE[1]) # The area of the ploted graph.
PLOT_SIZE = (0.95/130*GRAPH_SIZE_AREA[0],0.95/135*GRAPH_SIZE_AREA[1]) # The plot area for the fig part (matplotlib).
SUBSTANCE_DATABASE_SIZE = (int(WINDOW_SIZE[0]/64),int(WINDOW_SIZE[0]/384)) # The part of the substance window.

# Functions and setting:
# sg.theme('DarkBlue')
# sg.theme('DarkGrey2')
# sg.theme('Default')
sg.theme('DefaultNoMoreNagging')

#-------------------------------------------------------------------------------------------------

# This is for the Toolbar in the Interactive Window:
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

def draw_figure_w_toolbar(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg

#-------------------------------------------------------------------------------------------------

# Layouts:

# Allowing to show and not show the layout or the section according to events while running:
def collapse(layout, key, visible):
    # Hide or show the relevants fields.
    return sg.pin(sg.Column(layout, key=key, visible=visible))

def getGlobalColumn(norm_freq_list):
    # This function creates and return the layout of the upper toolbar with the filter settings.
    layout = [[sg.Checkbox("Filter", default=False, enable_events=True, key="_FILTER_CB_"), sg.Button("Filter\nConfiguration", size=(10,2), key="_FILT_CONF_"),
            sg.Push (), sg.Checkbox("Subtract Dark", default=False, enable_events=True, key="-MINUS_DARK-"), sg.Text("Dark Status:"), sg.Text("", key='darkStatus'), sg.Push(), sg.Checkbox("", enable_events=True, key='-Reg_Norm_Val-'), sg.Text("Normlize results by "), sg.Input(str(norm_freq_list[0]),enable_events=True,s=7,key="normValue"), sg.Text("[nm]"), sg.Push()], [sg.Push(), sg.Button("Apply", key='_APPLY_GLOBAL_', enable_events=True), sg.Text("Applied", key="_GLOBAL_STATUS_"), sg.Push()]]
    return layout

# The first layout:
def getSweepLayout(frequencyList, powerList, numIntervals):
    # This function creates and return the first plot layout – the layout of the first graph.
    # xAxis is a list of lists. Inputs must not be empty!
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Powers:"), sg.Push()],
            [sg.Push(), sg.Listbox(values=frequencyList, s=(14,10), enable_events=True, select_mode='single', key='_RepetitionListBoxSweepG_'),sg.Listbox(powerList, size=(14,10), enable_events=True, bind_return_key=True, select_mode='single', key='_PowerListBoxSweepG_'), sg.Push()]]
    menu_layout = [[sg.Push(), sg.Checkbox("Logarithmic Scale", default=True, enable_events=True, key="-REG_LOG_SCALE-"), sg.Push()],
            [sg.Push(),sg.Checkbox(text="Transmittance\ngraph",font='David 11',key="normCheckBox", enable_events=True, default=True), sg.Checkbox(text="Empty\nsample",font='David 11',key="cleanCheckBox",enable_events=True, default=False), sg.Checkbox(text="Non empty\nsample",font='David 11',key="substanceCheckBox", enable_events=True, default=False), sg.Push()],
            [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
            [sg.Push(), sg.Button("Clear All", key='-CLEAR_SWEEP_PLOT-', enable_events=True),sg.Push()]]
    graph_layout = [[sg.Canvas(key='controls_cv1')], [sg.Column(layout=[[sg.Canvas(key='figCanvas1',
            # it's important that you set this size
            size=(400 * 2, 400))]], background_color='#DAE0E6', pad=(0, 0))], [sg.Text('Graphs Interval')], [sg.Slider(range=(min(numIntervals), max(numIntervals)), size=(60, 10), orientation='h', key='-SLIDER-', resolution=1/(10*len(numIntervals))), sg.Button("Hold", key = '_HOLD_REG_', enable_events=True)]]
    Layout = [[sg.Push(), sg.Column(menu_layout, s=SETTING_AREA_SIZE), sg.Column(graph_layout, s=GRAPH_SIZE_AREA), sg.Push()]]
    return Layout

# The seconcd layout:
def getAllanDeviationLayout(frequencyList, powerList, norm_freq_list):
    # xAxis is a list of lists. Inputs must not be empty!
    database_Layout = [[sg.Text("Select data file")],
                [sg.Listbox(getDatabases(), select_mode='LISTBOX_SELECT_MODE_SINGLE', key="_DATA_FILE_", enable_events = True, size=SUBSTANCE_DATABASE_SIZE)]]
    sweepCompareSection = [[sg.Push(), sg.Text("Select Repetition:"), sg.Text("Select Power:"), sg.Push()],
                [sg.Push(), sg.Listbox(values=frequencyList, s=(14,5), enable_events=True, select_mode='single', key='_RepetitionListBoxAllanDG_'),sg.Listbox(powerList, size=(14,5), enable_events=True, bind_return_key=True, select_mode='single', key='_PowerListBoxAllanDG_'), sg.Push()]]
    absorbance_layout = [[sg.Push(), sg.Text("Help? This range will take the correct\nwavelength peak from the datafile of the substance"), sg.Push()],
                [sg.Checkbox(text="Values from the upper main toolbar",font='David 11',key="toolbarRange", enable_events=True, default=True)], [sg.Checkbox(text="Choose different range:",font='David 11',key="chooseRange", enable_events=True, default=False)],                 
                [sg.Push(), sg.Text("From: "), sg.Input("", key="from",s=7), sg.Text("to: "), sg.Input("", key='to', s=7), sg.Text("[nm]"), sg.Button("Set", 
                key='_data_wavelength_set_'), sg.Push()], [sg.Push(), sg.Text("The wavelength value to calculate: "), sg.Text("", key='_ABS_NM_'), sg.Text("nm"), sg.Push()]]
    menu_layout = [[sg.Push(), collapse(database_Layout, 'section_dataBaseValue', True), sg.Push()],
                [collapse([[sg.Frame("Peaks for data file - Concetration wavelength range:", absorbance_layout, key='helpRangeForPPM')]], 'section_AbsValue', False)],
                [sg.Push(), collapse(sweepCompareSection, 'section_sweepCompare', True), sg.Push()],
                [sg.Push(), sg.Text("Waveguide length"), sg.Input("", s=7, key='_WAVEGUIDE_LENGTH_', enable_events=True), sg.Text("mm"), sg.Push()],
                [sg.Push(), sg.Text("Gama Value"), sg.Input("1", s=7, key='_GAMA_', enable_events=True), sg.Push()],
                [sg.Push(), sg.Button("Add", key='_ADD_GRAPH_', enable_events=True), sg.Button("Hold", key='_HOLD_', enable_events=True), sg.Push()],
                [sg.Push(), sg.Button("Save to csv file", key='_CSV_', enable_events=True), sg.Input("csv file name", s=15, key='csvFileName'), sg.Push()],
                [sg.Push(), sg.Button("Clear All", key='-CLEAR_ALLAN_PLOT-', enable_events=True),sg.Push()],[sg.Push(), sg.Text("", key='timeIntervalText') ,sg.Push()],
                [sg.Push(), sg.Text("ppm", font='David 10'), sg.Slider(range=(0,1), orientation='h', key='_PPM_SLIDER_', resolution=1, size=(6,15), default_value = 0, enable_events=True), sg.Text("%", font='David 10'), sg.Push()]]
    graph_layout = [[sg.Canvas(key='controls_cv2')], [sg.Column(layout=[[sg.Canvas(key='figCanvas2',
                # it's important that you set this size
                size=(400 * 2, 200))]], background_color='#DAE0E6', pad=(0, 0))]]
    Layout = [[sg.Push(), sg.Column(menu_layout, s=SETTING_AREA_SIZE), sg.Column(graph_layout, s=GRAPH_SIZE_AREA), sg.Push()]]
    return Layout

def getRangeChoosingLayout(left, right):
    # Choose the range of the search location:
    cutoff_layout = [[sg.Text("Left Cutoff:"), sg.Push(), sg.Input(left, key='Lcutoff', s=15), sg.Text("nm")],
                [sg.Text("Right Cutoff:"), sg.Push(), sg.Input(right, key='Rcutoff', s=15), sg.Text("nm")]]
    layout = [[sg.Push(), sg.Text("This range will use to calculate the transmittance.") ,sg.Push()],
                [sg.Push(), sg.Text("Show peaks?"), sg.Text("No"), sg.Slider(range=(0,1), orientation='h', key='_PEAKS_SLIDER_', resolution=1, size=(6,15), default_value = 0, enable_events=True), sg.Text("Yes"), sg.Push()], [sg.Column(cutoff_layout), sg.Button("Set", key='cutoffSet')]]
    return layout

def filter_selection_window():
    butterworth_layout = [[sg.Text("Cutoff frequency:"), sg.Input('0.03', key='_cutoff_BW')],
                [sg.Text("Order:"), sg.Input('4', key='_order_BW')]]
    cheby1_layout = [[sg.Text("Cutoff frequency:"), sg.Input('0.03', key='_cutoff_cheby1')],
                [sg.Text("Order:"), sg.Input('4', key='_order_cheby1')],
                [sg.Text("Ripple [dB]:"), sg.Input('0.5', key='_ripple_cheby1')]]
    filter_selection_layout = [[sg.Combo(['BW', 'cheby1'], key='_FILTER_TYPE_', default_value='BW', enable_events = True)],
                [collapse(butterworth_layout, 'section_BW', True)],
                [collapse(cheby1_layout, 'section_cheby1', False)],
                [sg.Button('Ok'), sg.Button('Cancel')]]
    filter_window = sg.Window('Filter configurations', layout=filter_selection_layout, finalize=True)
    while True:
        event, values = filter_window.read()
        if event == 'Ok':
            filter_window.close()
            return values
        elif ( (event == 'Cancel') or (event == sg.WIN_CLOSED) ):
            filter_window.close()
            return False
        elif event == '_FILTER_TYPE_':
            if values['_FILTER_TYPE_'] == 'BW':
                filter_window['section_BW'].update(visible=True)
                filter_window['section_cheby1'].update(visible=False)
            elif values['_FILTER_TYPE_'] == 'cheby1':
                filter_window['section_BW'].update(visible=False)
                filter_window['section_cheby1'].update(visible=True)

# End of Layouts.

#---------------------------------------------------------------------------------------------------------------------------

# Additional functions:

def getTime():
    time = str(datetime.today())
    time = time.replace('-', '_')
    time = time.replace(' ', '_')
    time = time.replace(':', '_')
    time = time.replace('.', '_')
    return time

def setTitles(ax, scale, fig):           
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel(scale)
    # Update the plot scaling
    ax.relim()  # Recalculate the data limits
    ax.autoscale_view()  # Adjust the axis limits to fit the new data
    fig.draw()

def updateRegualrGraph(df_to_plot, ax, fig_agg, color, scale, data_type):
    line1 = False
    for i in range(len(df_to_plot)):
        try:
            label = '{}_{}_Power_{}%_TS {:.2f}'.format(data_type, df_to_plot['REP_RATE'].iloc[i], df_to_plot['POWER'].iloc[i], df_to_plot['Interval'].iloc[i])
            labels = [line.get_label() for line in ax.lines]
            if label not in labels:
                line1 = ax.plot(np.asarray(df_to_plot.columns[10:], float), df_to_plot.iloc[i,10:].values, label=label, color=color)
                # Add a legend
                line1 = line1[0]
            else:
                return False
        except:
            return False
    if (scale not in ['[dB]', '[dBm]']) and line1 != False:
        if scale == '[mW]':
            old_scale = '[dBm]'
        else:
            old_scale = '[dB]'
        y_data = line1.get_ydata()  # Get the y-data of the line
        new_y_data = convert_scale(y_data, old_scale)  # Apply the function to modify the y-data
        line1.set_ydata(new_y_data)  # Update the y-data of the line
    ax.legend(loc='upper right')
    fig_agg.draw()
    return line1

def add_reg_history(ax, hold_lines, fig_agg):
    ax.cla()
    ax.grid()
    if len(hold_lines) > 0:
        for line1 in hold_lines.values():
            ax.add_line(line1)
        ax.legend(loc='upper right')
        fig_agg.draw()

def getDatabases():
    try:
        filenames = os.listdir("..\\Databases")
    except:
        os.mkdir("..\\Databases")
        filenames = os.listdir("..\\Databases")
    filenames.sort()
    filenames = [name[:-4] for name in filenames]
    return filenames

def findValueInDatabase(data_file, left, right):
    try:
        df = pd.read_csv("..\\Databases\\" + data_file, names=['Wavenumber', 'Absorbance'], delimiter='\t')
    except:
        return False
    df['Wavelength'] = df['Wavenumber'].apply(lambda val: 10000000/val) # Adding a column of wavelength.
    if len(left) == 0:
        left = '0'
    if len(right) == 0:
        right = '0'
    filtered_df = df.loc[(df['Wavelength'] >= float(left)) & (df['Wavelength'] <= float(right))]
    if filtered_df.empty:
        return df.loc[df['Absorbance'] == df['Absorbance'].max(), 'Wavelength'].values[0]
    max_value = filtered_df['Absorbance'].max()
    max_absorbanceWavelength = filtered_df.loc[filtered_df['Absorbance'] == max_value, 'Wavelength'].values[0]
    return round(max_absorbanceWavelength, 2)

def get_datafile_range(filename):
    try:
        df = pd.read_csv("..\\Databases\\" + filename, names=['Wavenumber', 'Absorbance'], delimiter='\t')
    except:
        return False, False
    return str(10000000/df['Wavenumber'].iloc[0]), str(10000000/df['Wavenumber'].iloc[-1])

def get_maximum(data_file):
    with open("..\\Databases\\"+data_file, mode='r') as data:
        data = data.readlines()
    if len(data) == 0:
        return False
    maximum_A = float(data[0].split('\t')[1][:-1])
    maximum_WN = float(data[0].split('\t')[0])
    for line in data:
        A = float(line.split('\t')[1][:-1])
        WN = float(line.split('\t')[0])
        if A > maximum_A:
            maximum_A = A
            maximum_WN = WN
    return str(10000000/maximum_WN) # Convertion to [nm]

def saveAllanPlots(holdAllanDeviationList, new_allandeviation_line, csvFileName, dirname):
    holdAllanDeviationList[new_allandeviation_line._label] = new_allandeviation_line
    # Save deviation csv
    new_df = pd.DataFrame(columns=['Rep Rate', 'Power', 'Database file name', 'conentration wavelength [nm]', 'Waveguide Length [mm]', 'Averaging time [s]', 'Value'])
    for line in holdAllanDeviationList.values():
        temp_df = pd.DataFrame(columns=['Rep Rate', 'Power', 'Database file name', 'conentration wavelength [nm]', 'Waveguide Length [mm]', 'Averaging time [s]', 'Value'])
        label = line._label.split('_')
        rr = label[1][2:]
        p = label[0][1:]
        c = label[2][1:]
        wl = label[3][2:]
        wgl = label[4][3:]
        temp_df['Averaging time [s]'] = line.get_xdata()
        temp_df['Value'] = line.get_ydata()
        temp_df['Rep Rate'] = rr
        temp_df['Power'] = p
        temp_df['Waveguide Length [mm]'] = wgl
        temp_df['Database file name'] = c
        temp_df['conentration wavelength [nm]'] = wl
        new_df = pd.concat([new_df.loc[:],temp_df]).reset_index(drop=True)
    new_df.to_csv(dirname+getTime()+'_'+csvFileName+'.csv', index=False)

def convert_scale(y_data, old_scale):
    if old_scale == '[dB]':
        return [10**(val/10) for val in y_data]
    elif old_scale == '[dBm]':
        return [10**((val-30)/10) for val in y_data]
    elif old_scale == '[mW]':
        return [10*np.log10(val/(10**(-3))) for val in y_data]
    elif old_scale == 'Ratio':
        return [10*np.log10(val) for val in y_data]

def convert_reg_scale(lines_dict, old_scale, fig_agg, ax):
    for _, line in lines_dict.items():
        y_data = line.get_ydata()  # Get the y-data of the line
        new_y_data = convert_scale(y_data, old_scale)  # Apply the function to modify the y-data
        line.set_ydata(new_y_data)  # Update the y-data of the line
    fig_agg.draw() 

# The sweep graph functions parts
def clear_allan_plots(ax1,ax2,plotType):
    ax1.cla()
    ax2.cla()
    ax1.set_xlabel("Time [s]")
    ax2.set_xlabel("Averaging time [s]")
    if plotType:
        ax1.set_title("Concentration [%]")
    else:
        ax1.set_title("Concentration [ppm]")
    ax2.set_title("Allan Deviation")
    ax1.grid()
    ax2.grid(markevery=1)

def add_allanDeviation_history(ax_conc, ax_deviation, hold_lines_conc, hold_lines_dev, fig_agg):
    for line1 in hold_lines_conc.values():
        ax_conc.add_line(line1)
    ax_conc.legend(loc='upper right')
    for line1 in hold_lines_dev.values():
        ax_deviation.add_line(line1)
    ax_deviation.legend(loc='upper right')
    fig_agg.draw()

def check_files(csvFile):
    try:
        df_clean = pd.read_csv(csvFile + 'clean.csv', nrows=1)
    except:
        tkm.showerror(title="Problem reading 'clean' file!", message="There was a problem reading 'clean.csv' file.")
        return False
    try:
        df_substance = pd.read_csv(csvFile + 'substance.csv',  nrows=1)
    except:
        tkm.showerror(title="Problem reading 'substance' file!", message="There was a problem reading 'substance.csv' file.")
        return False

def clear_regular_sweep_plot(window, ax, values, scales_dict, fig1, fig_agg1, drawSweepGraph):
    window['_PowerListBoxSweepG_'].update(set_to_index=[])
    window['_RepetitionListBoxSweepG_'].update(set_to_index=[])
    ax.cla()
    ax.grid()
    hold_reg_lines = {} # deleting history
    colors_reg_Sweep = [name for name, hex in mcolors.CSS4_COLORS.items()
            if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors_reg_Sweep.pop(0)
    color_reg = colors_reg_Sweep[0]
    values['substanceCheckBox'] = False
    window['substanceCheckBox'].update(False)
    values['cleanCheckBox'] = False
    window['cleanCheckBox'].update(False)
    values['normCheckBox'] = True
    window['normCheckBox'].update(True)
    window['-REG_LOG_SCALE-'].update(True)
    scales = scales_dict["LOG"]
    scale = "[dB]"
    fig1, ax, fig_agg1,scales,scale = drawSweepGraph(fig1, ax, fig_agg1,scales,scale)
    line1 = False
    data_type = 'T'
    return hold_reg_lines, color_reg, colors_reg_Sweep, values, line1, data_type, fig1, ax, fig_agg1,scales,scale

def apply_function_animation(csvFile, values, filter_conf_vals):
    future = None
    animation = time.time()
    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
    while True:
        if (time.time() - animation > 0.05):
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
            animation = time.time()
        if future == None:
            future = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(get_clean_substance_transmittance, [csvFile, values['-MINUS_DARK-'], filter_conf_vals, values['-Reg_Norm_Val-'], values['normValue'], values['_FILTER_CB_']])
        if (future._state != 'RUNNING'):
            sg.PopupAnimated(None)
            break
    future = future.result()
    return future[0], future[1], future[2], future[3]
    
def convert_concentraion_units(ax_conc, fig_agg, ppm_slider):
    # ppm_slider = 0-ppm, 1-%
    lines = ax_conc.lines
    for line in lines:
        y_data = line.get_ydata()  # Get the y-data of the line
        if ppm_slider: # '1%' = 10,000ppm 
            new_y_data = [val/10000 for val in y_data]
            ax_conc.set_title("Concentration [%]")
        else:
            new_y_data = [val*10000 for val in y_data]
            ax_conc.set_title("Concentration [ppm]")
        line.set_ydata(new_y_data)  # Update the y-data of the line
    fig_agg.draw()

def getLinePeak(line, left, right):
    # Create DataFrame
    y_data = line.get_ydata()  # Get the y-data of the line
    x_data = line.get_xdata()  # Get the x-data of the line
    data = {"Wavelengths": x_data, "Values": y_data}
    df = pd.DataFrame(data)
    # Filter the DataFrame based on the wavelength range
    filtered_df = df.loc[(df['Wavelengths'] >= float(left)) & (df['Wavelengths'] <= float(right))]
    # Find the minimum value within the filtered range
    min_value = filtered_df['Values'].min()
    # Get the corresponding wavelength for the minimum value
    min_wavelength = filtered_df.loc[filtered_df['Values'] == min_value, 'Wavelengths'].values[0]
    return min_value, min_wavelength

def checkLeftRightWavelength(valuesLcutoff, valuesRcutoff ,Lcutoff, Rcutoff):
    # Checking cutoffs:
    # Edge cases:
    if len(valuesLcutoff) == 0:
        valuesLcutoff = '0'
    if len(valuesRcutoff) == 0:
        valuesRcutoff = '0'
    if len(Lcutoff) == 0:
        Lcutoff = '0'
    if len(Rcutoff) == 0:
        Rcutoff = '0'
    if float(valuesLcutoff) < float(Lcutoff):
        valuesLcutoff = Lcutoff
    if float(valuesRcutoff) > float(Rcutoff):
        valuesRcutoff = Rcutoff
    # Compare cases:
    if float(valuesLcutoff) > float(valuesRcutoff):
        if float(valuesRcutoff) < float(Lcutoff):
            valuesRcutoff = Lcutoff
        valuesLcutoff = valuesRcutoff
    # End of cutoffs check.
    return valuesLcutoff, valuesRcutoff

def addMinimumDots(ax, fig_agg1, left, right):
    peaks_x = []
    peaks_y = []
    for line in ax.lines:
        peak_x, peak_y = getLinePeak(line, left, right)
        peaks_x.append(peak_x)
        peaks_y.append(peak_y)
    ax.scatter(peaks_y, peaks_x, marker='o', color='red', s=100)
    fig_agg1.draw()

def deleteMinimumDots(ax, fig_agg1):
    # Get all artists on the axes
    artists = ax.get_children()
    # Filter and remove scatter plot markers from the axes
    for artist in artists:
        if isinstance(artist, clt.PathCollection):
            artist.remove()
    fig_agg1.draw()

#---------------------------------------------------------------------------------------------------------------------------

# This is the main function of the interactive graph:
def interactiveGraph(csvFile):
    # Variables initializations
    new_concentration_line = None   # holds last added line to concentration plot
    new_allandeviation_line = None  # holds last added line to allan deviation plot
    realWavelength = None           # When user inserts a wavelength, the realWavelength is closest wavelength exists in the data
    df_concentration = None         # the output of concentration calculation function
    holdConcentrationList = {}      # holds the history of concentration and deviation (next dict)
    holdAllanDeviationList = {}
    hold_reg_lines = {}
    sweepGraph = None               # layout of the sweepgraph window
    allan_and_concentration = None  # layout of the concentration window
    flag_allan = True
    line1 = False
    data_type = 'T'
    
    colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                if np.mean(mcolors.hex2color(hex)) < 0.7]
    colors_allanDeviationConcentration.pop(0)
    colors_reg_Sweep = colors_allanDeviationConcentration.copy()
    color_reg = colors_reg_Sweep[0]
    color = colors_allanDeviationConcentration[0]
    
    scales_dict = {"LOG": {"CLEAN": "[dBm]", "SUBSTANCE": "[dBm]", "RATIO": "[dB]"}, "WATT":{"CLEAN": "[mW]", "SUBSTANCE": "[mW]", "RATIO": "Ratio"}}
    scales_dict_converter = {'[dBm]': '[mW]', '[dB]': 'Ratio', '[mW]': '[dBm]', 'Ratio': '[dB]'}
    
    #-------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    check = check_files(csvFile)
    if check == False:
        return False
    
    df_ratio, df_clean, df_substance, darkStatus = apply_function_animation(csvFile, {'-MINUS_DARK-': False, '-Reg_Norm_Val-': False, 'normValue': '1500', '_FILTER_CB_': False}, None)
    df_transmittance = df_ratio.copy()
    frequencyList = df_ratio['REP_RATE'].unique().tolist()
    powerList = df_ratio['POWER'].unique().tolist()
    norm_freq_list = np.asarray(df_ratio.columns[10:].tolist(), float)
    df_plotted_full = df_ratio

    # This is the main Layout - connect all the previous layouts:
    interval_list = list(df_transmittance['Interval'].loc[(df_transmittance['POWER'] == df_transmittance.iloc[0]['POWER']) & (df_transmittance['REP_RATE'] == df_transmittance.iloc[0]['REP_RATE'])].values)
    sweepGraph = getSweepLayout(frequencyList, powerList, interval_list)
    
    if len(df_clean) == len(df_substance):
        flag_allan = False
    if flag_allan:
        allan_and_concentration = getAllanDeviationLayout(frequencyList, powerList, norm_freq_list) 
    else:
        allan_and_concentration = [[sg.Push(), sg.Text("Allan Deviation & Concentration Graphs", font=("David", 20, "bold")),sg.Push()],
            [sg.Push(), sg.Text('There was a problem to read the correct file!'), sg.Push()]]
    
    layout = [[sg.Frame("Sweep Graph", sweepGraph, visible=True, key='section_sweepGraph', size=(FRAME_SIZE[0], FRAME_SIZE[1]))],
        [sg.Frame("Allan Deviation & Concentration", allan_and_concentration, visible=True, key='section_Allan_Concentration', size=(FRAME_SIZE[0], FRAME_SIZE[1]))]]
    
    wavelengthList = df_clean.columns.to_list()
    Lcutoff = str(round(float(wavelengthList[10]), 2)) # The minimum left wavelength possible in the range.
    Rcutoff = str(round(float(wavelengthList[-1]), 2)) # The maximum right wavelength possible in the range.
    range_choosing_layout = getRangeChoosingLayout(Lcutoff, Rcutoff)
    global_layout = getGlobalColumn(norm_freq_list)
    general_Buttons_layout = [[sg.Push(), sg.Button("Reset All", key = 'Are you sure? (Yes, Reset)'), sg.Push()], [sg.Push(), sg.Button("Close", key = 'Close Graph'), sg.Push()]]

    main_Layout = [
            [sg.Push(), sg.Frame("Peaks", range_choosing_layout, visible=True, key='section_choose_range'), sg.Frame("Configurations", global_layout, visible=True, key='section_global_conf'), sg.Frame("General Buttons", general_Buttons_layout, visible=True, key='section_global_buttons'), sg.Push()],
            [sg.Push(), sg.Text('Results of: '+csvFile, justification='center', background_color='#7393B3', expand_x=False, font=("David", 15, "bold")), sg.Push()],
            [sg.Column(layout, scrollable=True, vertical_scroll_only=True, key='COLUMN')]]
    
    window = sg.Window("Interactive Graph", main_Layout, size=(WINDOW_SIZE[0], WINDOW_SIZE[1]), finalize=True)
    
    # Parameters for the functions:
    fig1 = None
    fig2 = None
    fig_agg1 = None
    fig_agg2 = None
    scales = None
    scale = None
    ax = None
    ax_conc = None
    ax_deviation = None
    filter_conf_vals = None
    slider_elem = window['-SLIDER-']
    window['-SLIDER-'].bind('<ButtonRelease-1>', ' Release')
    # End of Parameters for the functions.

    # Sweep Graph - Start:
    def drawSweepGraph(fig1, ax, fig_agg1,scales,scale):
        # Creating the automatic first graph:
        plt.ioff()
        fig1 = plt.figure()
        plt.ion() 
        fig1.set_figwidth(PLOT_SIZE[0])
        fig1.set_figheight(PLOT_SIZE[1])
        ax = fig1.add_subplot(111)
        ax.set_xlabel("Wavelength [nm]")
        ax.grid()
        fig_agg1 = draw_figure_w_toolbar(window['figCanvas1'].TKCanvas, fig1, window['controls_cv1'].TKCanvas)
        plt.title('No Plot to show. Choose data...')
        scales = scales_dict["LOG"]
        scale = "[dB]"
        if darkStatus:
            window['darkStatus'].update("OK")
        else:
            window['darkStatus'].update("'dark.csv' not Found")
        return fig1, ax, fig_agg1,scales,scale
    # Sweep Graph - End.

    # Allan Deviation - Start:
    def drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2):
        # Creating the automatic first graph:
        plt.ioff()
        fig2 = plt.figure()
        plt.ion()
        fig2.set_figwidth(PLOT_SIZE[0])
        fig2.set_figheight(PLOT_SIZE[1])
        ax_deviation = fig2.add_subplot(211)
        ax_deviation.set_title("Allan Deviation")
        ax_deviation.grid(markevery=1)
        ax_conc = fig2.add_subplot(212)
        ax_conc.set_xlabel("Time [s]")
        ax_deviation.set_xlabel("Averaging time [s]")
        ax_conc.set_title("Concentration [ppm]")
        ax_conc.grid()
        fig_agg2 = draw_figure_w_toolbar(window['figCanvas2'].TKCanvas, fig2, window['controls_cv2'].TKCanvas)
        fig2.tight_layout(pad=5.0)
        return fig2, ax_conc, ax_deviation, fig_agg2
        # End of creating the graph.
    # Allan Deviation - End.

    # First Start:
    fig1, ax, fig_agg1,scales,scale = drawSweepGraph(fig1, ax, fig_agg1,scales,scale)
    if flag_allan:
        fig2, ax_conc, ax_deviation, fig_agg2 = drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2)

    # Start checking the events:
    while True:

        event, values = window.read()

        # Closing the graph.
        if ( (event == 'Close Graph') or (event == sg.WIN_CLOSED) ):
            window.close()
            break

        elif event == '_FILTER_CB_' or event == '_FILT_CONF_' or event == '-MINUS_DARK-' or event == '-Reg_Norm_Val-' or event == 'normValue':
            window['_GLOBAL_STATUS_'].update("Not Applied")
            if event == '_FILT_CONF_':
                filter_conf_vals = filter_selection_window()
        
        elif event == '_APPLY_GLOBAL_':
            # How to apply BW filter:
            if filter_conf_vals == None and values['_FILTER_CB_']:
                filter_conf_vals = filter_selection_window()
            df_ratio, df_clean, df_substance, darkStatus = apply_function_animation(csvFile, values, filter_conf_vals)
            df_transmittance = df_ratio.copy()
            frequencyList = df_ratio['REP_RATE'].unique().tolist()
            powerList = df_ratio['POWER'].unique().tolist()
            norm_freq_list = np.asarray(df_ratio.columns[10:].tolist(), float)
            window['_GLOBAL_STATUS_'].update("Applied")
            hold_reg_lines, color_reg, colors_reg_Sweep, values, line1, data_type, fig1, ax, fig_agg1,scales,scale = clear_regular_sweep_plot(window, ax, values, scales_dict, fig1, fig_agg1, drawSweepGraph)
            df_plotted_full = df_ratio
            if values['-MINUS_DARK-'] and darkStatus:
                window['darkStatus'].update("OK")
            elif values['-MINUS_DARK-'] and (darkStatus == False):
                window['darkStatus'].update("'dark.csv' not Found")
            elif values['-MINUS_DARK-']==False and (darkStatus == False):
                window['darkStatus'].update("Calculation ignoring dark measurment")
            elif values['-MINUS_DARK-']==False and (darkStatus == True):
                window['darkStatus'].update("No way! No sense")
            
        # Reset all and clear all:
        elif event == 'Are you sure? (Yes, Reset)':
            hold_reg_lines, color_reg, colors_reg_Sweep, values, line1, data_type, fig1, ax, fig_agg1,scales,scale = clear_regular_sweep_plot(window, ax, values, scales_dict, fig1, fig_agg1, drawSweepGraph)
            df_plotted_full = df_ratio
            if flag_allan:
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                window['_PowerListBoxAllanDG_'].update(set_to_index=[])
                window['_RepetitionListBoxAllanDG_'].update(set_to_index=[])
                clear_allan_plots(ax_conc, ax_deviation, values['_PPM_SLIDER_'])
                new_concentration_line = None
                new_allandeviation_line = None
                holdConcentrationList = {}
                holdAllanDeviationList = {}
                colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_allanDeviationConcentration.pop(0)
                color = colors_allanDeviationConcentration[0]
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
                fig2, ax_conc, ax_deviation, fig_agg2 = drawAllanDeviationGraph(fig2, ax_conc, ax_deviation, fig_agg2)
            # End of Reset.

    # This part is for the sweep graph:
            
        # Clear the graph and the relevant parametrs.
        elif event == '-CLEAR_SWEEP_PLOT-':
            hold_reg_lines, color_reg, colors_reg_Sweep, values, line1, data_type, fig1, ax, fig_agg1,scales,scale = clear_regular_sweep_plot(window, ax, values, scales_dict, fig1, fig_agg1, drawSweepGraph)
            df_plotted_full = df_ratio

        elif event == '-SLIDER- Release':
            interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_']) & (df_plotted_full['Interval'] == interval)]
            if len(df_plotted) == 0:
                continue
            add_reg_history(ax, hold_reg_lines, fig_agg1)
            line1 = updateRegualrGraph(df_plotted, ax, fig_agg1, color_reg, scale, data_type)
        
        elif (event == '_RepetitionListBoxSweepG_') or (event == '_PowerListBoxSweepG_'):
            interval_list = list(df_plotted_full['Interval'].loc[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])].values)
            try:
                interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
            except:
                continue
            df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_']) & (df_plotted_full['Interval'] == interval)]
            if len(df_plotted) == 0:
                continue
            slider_elem.Update(range=(min(df_plotted_full['Interval'].loc[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]), max(df_plotted_full['Interval'].loc[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])])))
            add_reg_history(ax, hold_reg_lines, fig_agg1)
            line1 = updateRegualrGraph(df_plotted, ax, fig_agg1, color_reg, scale, data_type)
        
        elif event == '_HOLD_REG_':
            if line1 != False:
                hold_reg_lines[line1._label] = line1
                colors_reg_Sweep.remove(color_reg)
                color_reg = colors_reg_Sweep[0]
        
        elif (event == '-REG_LOG_SCALE-'):
            window3 = sg.Window("Processing...", [[sg.Text("Changing graph scale, please wait...")]], finalize=True)
            if values['-REG_LOG_SCALE-']:
                scales = scales_dict["LOG"]
            else:
                scales = scales_dict["WATT"]
            new_dict = hold_reg_lines.copy()
            if line1 != False:
                new_dict[line1._label] = line1
            convert_reg_scale(new_dict, scale, fig_agg1, ax)
            # Update the plot scaling
            ax.relim()  # Recalculate the data limits
            ax.autoscale_view()  # Adjust the axis limits to fit the new data
            scale = scales_dict_converter[scale]
            window3.close()

        elif (event == 'cleanCheckBox'):
            ax.cla()
            ax.grid()
            if values['-REG_LOG_SCALE-']:
                scales = scales_dict["LOG"]
            else:
                scales = scales_dict["WATT"]
            scale = scales['CLEAN']    
            if (values['cleanCheckBox']):
                values['substanceCheckBox'] = False
                values['normCheckBox'] = False                                      
                window['substanceCheckBox'].update(False)
                window['normCheckBox'].update(False)
                data_type = 'C'
                df_plotted_full = df_clean
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) == 0:
                    continue
                new_range = (min(df_plotted['Interval']), max(df_plotted['Interval']))
                interval_list = df_plotted['Interval'].tolist()
                slider_elem.Update(range=new_range)
                interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
                add_reg_history(ax, hold_reg_lines, fig_agg1)
                line1 = updateRegualrGraph(df_plotted[df_plotted['Interval'] == interval], ax, fig_agg1, color_reg, scale, data_type)

        elif (event == 'substanceCheckBox'):
            ax.cla()
            ax.grid()
            if values['-REG_LOG_SCALE-']:
                scales = scales_dict["LOG"]
            else:
                scales = scales_dict["WATT"]
            scale = scales['SUBSTANCE']
            if (values['substanceCheckBox']):
                values['cleanCheckBox'] = False
                values['normCheckBox'] = False
                window['cleanCheckBox'].update(False)                              
                window['normCheckBox'].update(False)
                data_type = 'S'
                df_plotted_full = df_substance
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) == 0:
                    continue
                new_range = (min(df_plotted['Interval']), max(df_plotted['Interval']))
                interval_list = df_plotted['Interval'].tolist()
                slider_elem.Update(range=new_range)
                interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
                add_reg_history(ax, hold_reg_lines, fig_agg1)
                line1 = updateRegualrGraph(df_plotted[df_plotted['Interval'] == interval], ax, fig_agg1, color_reg, scale, data_type)
                
        elif (event == 'normCheckBox'):
            ax.cla()
            ax.grid()
            if values['-REG_LOG_SCALE-']:
                scales = scales_dict["LOG"]
            else:
                scales = scales_dict["WATT"]
            scale = scales['RATIO']
            if (values['normCheckBox']):
                values['cleanCheckBox'] = False                                      
                values['substanceCheckBox'] = False
                window['cleanCheckBox'].update(False)
                window['substanceCheckBox'].update(False)
                data_type = 'T'
                df_plotted_full = df_ratio
                df_plotted = df_plotted_full[df_plotted_full['REP_RATE'].isin(values['_RepetitionListBoxSweepG_']) & df_plotted_full['POWER'].isin(values['_PowerListBoxSweepG_'])]
                if len(df_plotted) == 0:
                    continue
                new_range = (min(df_plotted['Interval']), max(df_plotted['Interval']))
                interval_list = df_plotted['Interval'].tolist()
                slider_elem.Update(range=new_range)
                interval = interval_list[np.argmin([abs(values['-SLIDER-']-element) for element in interval_list])]
                add_reg_history(ax, hold_reg_lines, fig_agg1)
                line1 = updateRegualrGraph(df_plotted[df_plotted['Interval'] == interval], ax, fig_agg1, color_reg, scale, data_type)
                
        setTitles(ax, scale, fig_agg1)
    # End of sweep graph.

    # This part is for allan deviation & concentration part:

        if flag_allan:
        
            # Clear the graph and the relevant parametrs.
            if event == '-CLEAR_ALLAN_PLOT-':
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                window['_PowerListBoxAllanDG_'].update(set_to_index=[])
                window['_RepetitionListBoxAllanDG_'].update(set_to_index=[])
                clear_allan_plots(ax_conc, ax_deviation, values['_PPM_SLIDER_'])
                new_concentration_line = None
                new_allandeviation_line = None
                holdConcentrationList = {}
                holdAllanDeviationList = {}
                colors_allanDeviationConcentration = [name for name, hex in mcolors.CSS4_COLORS.items()
                    if np.mean(mcolors.hex2color(hex)) < 0.7]
                colors_allanDeviationConcentration.pop(0)
                color = colors_allanDeviationConcentration[0]
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
            
            elif event == 'toolbarRange':
                if values['toolbarRange']:
                    values['chooseRange'] == False
                    window['chooseRange'].update(False)
                    window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['Lcutoff'], values['Rcutoff'])))

            elif event == 'chooseRange':
                if values['chooseRange']:
                    values['toolbarRange'] = False
                    window['toolbarRange'].update(False)
                    event = '_DATA_FILE_'

            elif event == '_ADD_GRAPH_':
                if (len(values['_RepetitionListBoxAllanDG_']) > 0) and (len(values['_PowerListBoxAllanDG_']) > 0)  and (len(values['_DATA_FILE_']) > 0) and (values['_WAVEGUIDE_LENGTH_'] != '') and (values['toolbarRange'] or values['chooseRange']):   # To add protection to the length try: float except ->float
                    # All the logic of working Animation is starting:
                    window['_ADD_GRAPH_'].update(disabled=True)
                    window['_HOLD_'].update(disabled=True)
                    window['_CSV_'].update(disabled=True)
                    window['-CLEAR_ALLAN_PLOT-'].update(disabled=True)
                    window['Close Graph'].update(disabled=True)
                    future2 = None
                    future3 = None
                    Operation_State = 0 # 0-beerlambert, 1-allandeviation
                    animation = time.time()
                    sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                    # Check the range of the wavelength in the 'Range choosing' tab.
                    values['Lcutoff'], values['Rcutoff'] = checkLeftRightWavelength(values['Lcutoff'], values['Rcutoff'] ,Lcutoff, Rcutoff)
                    window['Lcutoff'].update(values['Lcutoff'])
                    window['Rcutoff'].update(values['Rcutoff'])
                    values['from'], values['to'] = checkLeftRightWavelength(values['from'], values['to'] ,Lcutoff_datafile, Rcutoff_datafile)
                    if values['toolbarRange']:
                        window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['Lcutoff'], values['Rcutoff'])))
                    else: 
                        window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['from'], values['to'])))
                    if values['from'] == values['to']:
                        values['from'] = Lcutoff_datafile
                        values['to'] = Rcutoff_datafile
                    window['from'].update(values['from'])
                    window['to'].update(values['to'])
                    #
                    while True:
                        if (time.time() - animation > 0.05):
                            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=50)
                            animation = time.time()
                        #
                        if (Operation_State == 0):
                            if future2 == None:
                                if values['toolbarRange']:
                                    future2 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(beerLambert, [csvFile, "..\\Databases\\"+values['_DATA_FILE_'][0]+'.txt', float(window['_ABS_NM_'].get()), float(values['_WAVEGUIDE_LENGTH_']), values['_GAMA_'], df_transmittance, values['Lcutoff'], values['Rcutoff']])
                                if values['chooseRange']:
                                    future2 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(beerLambert, [csvFile, "..\\Databases\\"+values['_DATA_FILE_'][0]+'.txt', float(window['_ABS_NM_'].get()), float(values['_WAVEGUIDE_LENGTH_']), values['_GAMA_'], df_transmittance, values['from'], values['to']])
                                #future2 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(beerLambert, [csvFile, "..\\Databases\\"+values['_DATA_FILE_'][0]+'.txt',findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['from'], values['to']), float(values['_WAVEGUIDE_LENGTH_']), values['_GAMA_'], df_transmittance, values['Lcutoff'], values['Rcutoff']])
                            elif future2._state != 'RUNNING':
                                future2 = future2.result()
                                df_concentration = future2[0]
                                realWavelength = future2[1]
                                Operation_State = 1
                        #
                        elif (Operation_State == 1):
                            if future3 == None:
                                df_plotted = df_concentration[df_concentration['REP_RATE'].isin(values['_RepetitionListBoxAllanDG_']) & df_concentration['POWER'].isin(values['_PowerListBoxAllanDG_'])]
                                future3 = concurrent.futures.ThreadPoolExecutor(max_workers=100).submit(allandevation, df_plotted)
                            elif future3._state != 'RUNNING':
                                future3 = future3.result()
                                tau = future3[0] # Everytime is calculating.
                                adev = future3[1] # Everytime is calculating.
                                mean_interval = future3[2]
                                sg.PopupAnimated(None)
                                break

                    # End of the logic of working Animation.
                    label = 'p{}_rr{}_c{}_wl{:.2f}_wgl{:.2f}'.format(values['_PowerListBoxAllanDG_'][0], values['_RepetitionListBoxAllanDG_'][0], values['_DATA_FILE_'][0].replace('_','-'), float(realWavelength), float(values['_WAVEGUIDE_LENGTH_']))
                    if values['-Reg_Norm_Val-'] == True:
                        label = label + '_norm' + values['normValue']
                    if values['-MINUS_DARK-'] and darkStatus == True:
                        label = label + '_minusdark'
                    clear_allan_plots(ax_conc, ax_deviation, values['_PPM_SLIDER_'])
                    add_allanDeviation_history(ax_conc,ax_deviation,holdConcentrationList,holdAllanDeviationList,fig_agg2)
                    new_allandeviation_line = ax_deviation.loglog(tau, adev, label=label, color = color)
                    if (values['_PPM_SLIDER_']):
                        new_concentration_line = ax_conc.plot(df_plotted['Interval'], np.asarray(df_plotted['Concentration [%]'], float), label=label, color = color)
                    else:
                        new_concentration_line = ax_conc.plot(df_plotted['Interval'], np.asarray(df_plotted['Concentration [ppm]'], float), label=label, color = color)
                    ax_deviation.grid(which='minor', alpha=0.2, linestyle='--')
                    ax_deviation.grid(which='major', alpha=1, linestyle='-')
                    ax_conc.grid(which='minor', alpha=0.2)
                    ax_conc.grid(which='major', alpha=1)
                    ax_deviation.legend(loc='upper right')
                    ax_conc.legend('', frameon=False)
                    timeIntervalT = "The avarage Time Interval is: "+str("{:.3f}".format(mean_interval))+" seconds."
                    window['timeIntervalText'].update(timeIntervalT)
                    new_concentration_line = new_concentration_line[0]
                    new_allandeviation_line = new_allandeviation_line[0]
                    # Show the two Graphs:
                    fig_agg2.draw()
                else:
                    sg.popup_ok("Make sure the parameters are chosen correctly")
                window['_ADD_GRAPH_'].update(disabled=False)
                window['_HOLD_'].update(disabled=False)
                window['_CSV_'].update(disabled=False)
                window['-CLEAR_ALLAN_PLOT-'].update(disabled=False)
                window['Close Graph'].update(disabled=False)
                        
            elif event == '_HOLD_':
                window['_HOLD_'].update(disabled=True)
                if (new_concentration_line != None) and (new_allandeviation_line != None):
                    if ((new_concentration_line._label in holdConcentrationList) or (new_allandeviation_line._label in holdAllanDeviationList) ):
                        sg.popup_auto_close("The graph already exist in database.", title="Graph Exist", auto_close_duration=2)
                    else:
                        holdConcentrationList[new_concentration_line._label] = new_concentration_line
                        holdAllanDeviationList[new_allandeviation_line._label] = new_allandeviation_line
                        colors_allanDeviationConcentration.remove(color)
                        color = colors_allanDeviationConcentration[0]
                        new_concentration_line = None
                        new_allandeviation_line = None
                        # Site link: https://www.tutorialspoint.com/pysimplegui/pysimplegui_popup_windows.htm
                        sg.popup_auto_close("The selected graph was added.", title="Graph was added", auto_close_duration=1)
                else:
                    sg.popup_auto_close("The selected graph was already added.", title="Already added", auto_close_duration=2)
                window['_HOLD_'].update(disabled=False)

            elif event == '_CSV_':
                window['_CSV_'].update(disabled=True)
                saveAllanPlots(holdAllanDeviationList, new_allandeviation_line, values['csvFileName'], csvFile)
                csvFileWasSaved = '\'' + values['csvFileName'] + '.csv\' file was saved'
                window['csvFileName'].update("csv file name")
                sg.popup_auto_close(csvFileWasSaved, title="CSV File Saved", auto_close_duration=2)
                window['_CSV_'].update(disabled=False)

            elif event == '_PPM_SLIDER_':
                convert_concentraion_units(ax_conc, fig_agg2, values['_PPM_SLIDER_'])

            elif event == 'cutoffSet':
                # Check the range of the wavelength in the 'Range choosing' tab.
                values['Lcutoff'], values['Rcutoff'] = checkLeftRightWavelength(values['Lcutoff'], values['Rcutoff'] , Lcutoff, Rcutoff)
                window['Lcutoff'].update(values['Lcutoff'])
                window['Rcutoff'].update(values['Rcutoff'])
                if values['toolbarRange']:
                    window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['Lcutoff'], values['Rcutoff'])))
            
            elif event == '_data_wavelength_set_':
                values['from'], values['to'] = checkLeftRightWavelength(values['from'], values['to'] , Lcutoff_datafile, Rcutoff_datafile)
                window['from'].update(values['from'])
                window['to'].update(values['to'])
                if values['chooseRange']:
                    window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['from'], values['to'])))

            if event == '_DATA_FILE_':
                if len(values['_DATA_FILE_']) > 0:
                    window['section_AbsValue'].update(visible=True)
                    Lcutoff_datafile, Rcutoff_datafile = get_datafile_range(values['_DATA_FILE_'][0]+'.txt')
                    values['from'] = Lcutoff_datafile
                    values['to'] = Rcutoff_datafile
                    window['from'].update(values['from'])
                    window['to'].update(values['to'])
                    window['_ABS_NM_'].update("{:.2f}".format(findValueInDatabase(values['_DATA_FILE_'][0]+'.txt', values['from'], values['to'])))
                else:
                    window['section_AbsValue'].update(visible=False)

            if values['_PEAKS_SLIDER_'] == 1:
                # Check the range of the wavelength in the 'Range choosing' tab.
                values['Lcutoff'], values['Rcutoff'] = checkLeftRightWavelength(values['Lcutoff'], values['Rcutoff'] ,Lcutoff, Rcutoff)
                window['Lcutoff'].update(values['Lcutoff'])
                window['Rcutoff'].update(values['Rcutoff'])
                # Cutoffs already checked.
                deleteMinimumDots(ax, fig_agg1)
                addMinimumDots(ax, fig_agg1, values['Lcutoff'], values['Rcutoff'])
            else: # values['_PEAKS_SLIDER_'] == 0: Delete the dots.
                deleteMinimumDots(ax, fig_agg1)

            # Update the plot scaling
            ax_conc.relim()  # Recalculate the data limits
            ax_conc.autoscale_view()  # Adjust the axis limits to fit the new data
            fig_agg2.draw()

        # End of allan deviation & concentration graph.
    # End of main while.
# End of interactiveGraph function.

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------

# if __name__ == '__main__':
#     dirName = "..\\Results\\Recent_Measurements\\"
#     freeze_support()
#     Process(target=interactiveGraph, args=(dirName, )).start()

#--------------------------------------------------------------------------

# # For our checking:
# if __name__ == '__main__':
#     # Create the argument parser
#     parser = argparse.ArgumentParser(description='Plot graphs')

#     # Add arguments
#     parser.add_argument('--csv_name', type=str)
#     parser.add_argument('--analyzer_substance', type=bool)

#     # Parse the arguments
#     args = parser.parse_args()

#     if args.csv_name == None:
#         dirname = "..\\Results\\Recent_Measurements\\"
#         args.csv_name = dirname
#         args.analyzer_substance = False
#     interactiveGraph(args.csv_name)

# # End of 'Interactive_Graph.py' file.