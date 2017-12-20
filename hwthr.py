##
## Raspberry Pi Clock & Weather Display (rpi_clock)
## taken from https://github.com/texadactyl/rpi_clock
## Modified by Larry Bonnette 12/2017 to extract data from home Raspberry Pi weather station.
## and display on a TFT display
##---------------------------------------------------------------
## Data extracted from weather station looks like the following:
# {"FullDataString": "24.5,83.5,25.6,101556.0,50.63,07.4,18.6,180.0,0.09,3.33,6.98,6.30,11.21,90.00,135.00,0,
# 2017-12-19 11:37:33,,0,-1,4.04,-54.00,4.92,93.20,5.15,24.00,0.00,0.00,0.00,0.00,0.00,0.00,V:1,NONE ,", 
# "id": "1", "name": "HomeWeather", "connected": true}
#---------------------------------------------------------------
# We extract the data starting from the '"' counting the commas. The data before the first comma 1 = Outside Temperature 'C'
# comma 2 = Humidity, 3 = Indoor temp 'C', 4 = Barometric pressure hpa, 5 = Altitude k, 6 = current wind speed kph, 7 = wind gust kph, 8 = rain total, ........16 = Date and Time
##--------------------------------------------------------------

import os, time, sys, subprocess, json

MYNAME = 'home_weather'
flag_debugging = True
SLEEP_TIME_SEC = 60
SLEEP_TIME_MSEC = SLEEP_TIME_SEC*1000 # milliseconds

# ----------------------------------------------------------
# Weather station url info
FULL_URL = 'http://192.168.0.196/wthrdata.dat'
URL_REQUEST_TIMEOUT_SEC = 60
COUNT_START = 20 # Fetch weather every 20th main loop execution
count_down = 0 # Fetch weather data from URL_LEFT when =0
flag_url = False
str_temp = 'No temperature yet'
str_humidity = 'No condition yet'
comma_no = 0

# ----------------------------------------------------------
# Video display parameters
WINDOW_SIZE_ROOT = "480x320"
WINDOW_SIZE_POPUP = "320x200"
FONT_NAME = 'helvetica'
FONT_SIZE = 40
FONT_POPUP_SIZE = 24
FONT_STYLE = 'normal'
SPACER_SIZE = 20
BUTTON_WIDTH = 6
BUTTON_HEIGHT = 2
FG_COLOR_NORMAL = 'white'
FG_COLOR_ABNORMAL = 'red'
BG_COLOR_ROOT = 'black'
BG_COLOR_POPUP = BG_COLOR_ROOT
FORMAT_DATE = "%b %d, %Y" # USA date format
FORMAT_TIME = "%I:%M %p %Z" # Hours:Minutes + AM/PM for the USA

# ----------------------------------------------------------

# Time-stamp logger; API is like C-language printf
def logger(arg_format, *arg_list):
        now = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        fmt = "{nstr} {fstr}".format(nstr=now, fstr=arg_format)
        print(fmt % arg_list)
        sys.stdout.flush()

# ----------------------------------------------------------
# Exit immediately if this is an SSH session
if 'SSH_CLIENT' in os.environ or 'SSH_TTY' in os.environ:
        logger("%s: Running in SSH session; exiting", MYNAME)
        exit(0)

# ----------------------------------------------------------
# Must be Python 3.x
if sys.version_info[0] < 3:
        logger("%s: *** Requires Python 3", MYNAME)
        exit(86)

# ----------------------------------------------------------
# Import Python 3 libraries
from tkinter import *
import urllib.request

#-------------------------------------------------------------------
# comma index function
# returns the index number of a comma
# "needle" defines the charater we want to find. "haystack" is the text we will search through.
# "n" is the number of "," we want to find. "start" holds the index number into the text we want to return back to the program.

def getcomma(haystack,n):
        needle = ','
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start

#-------------------------------------------------------------------
# Talk to operator

def proc_exitr():

        sys.exit()

def talk_to_operator(event):
        if flag_debugging:
                logger("%s: DEBUG talk_to_operator begin", MYNAME)
        tk_popup = Tk()
        tk_popup.title("Exit App")
        tk_popup.attributes("-fullscreen", False)
        tk_popup.configure(background=BG_COLOR_POPUP)
        tk_popup.geometry(WINDOW_SIZE_POPUP)
        b_goback = Button(tk_popup, text="Go Back", command=tk_popup.destroy,
                 font=(FONT_NAME, FONT_POPUP_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL)
        b_goback.focus_set()
        b_goback.pack(fill="both", expand=True)
        b_EXITR = Button(tk_popup, text='Exit', command=proc_exitr,
                                        font=(FONT_NAME, FONT_POPUP_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL)
        b_EXITR.pack(fill="both", expand=True)
        if flag_debugging:
                logger("%s: DEBUG talk_to_operator going back to tk_popup.mainloop", MYNAME)
        tk_popup.mainloop()
        logger("%s: tk_popup left mainloop", MYNAME)

# ----------------------------------------------------------
# Initialize Tk
tk_root = Tk()
tk_root.attributes("-fullscreen", True)
# set BG color and turn off cursor
tk_root.configure(background=BG_COLOR_ROOT,cursor='none')
tk_root.geometry(WINDOW_SIZE_ROOT)
display_spacer1 = Label(tk_root, font=(FONT_NAME, SPACER_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL,bg=BG_COLOR_ROOT)
display_spacer1.pack()
display_spacer1.config(text=" ")

# ----------------------------------------------------------
# Build display lines
display_date = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_date.pack()

display_time = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_time.pack()

display_cur_temp = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_cur_temp.pack()

display_cur_cond = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_cur_cond.pack()

display_spacer2 = Label(tk_root, font=(FONT_NAME, SPACER_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_spacer2.pack()
display_spacer2.config(text=" ")

# ----------------------------------------------------------
# Procedure: Get date, time, farenheit-temperature, and celsius-temperature
def get_display_data():
        global count_down, str_temp, str_humidity, flag_url
        if flag_debugging:
                logger("%s: DEBUG get_display_data begin", MYNAME)
                logger("%s: DEBUG count_down state = " + str(count_down), MYNAME)
        if count_down < 1:
                # Time to go geat new weather data
                count_down = COUNT_START
                try:
                        url_handle = urllib.request.urlopen(FULL_URL, None, URL_REQUEST_TIMEOUT_SEC)
                        data = url_handle.read()
                        encoding = url_handle.info().get_content_charset('utf-8')
                        parsed_json = json.loads(data.decode(encoding))
                        str_wthrdat = parsed_json['FullDataString'] # places weather data into variable
                        comma_no = getcomma(str_wthrdat,1)          # We want the outdoor temperature which is just before the first comma.
                        str_temp = str_wthrdat[comma_no-4:comma_no] # We use the index number returned to extract the outdoor temperature
                        str_temp = ('%.2f' % ((float(str_temp) * 1.8) + 32)) # Convert "C" to Farenheite
                        comma_no = getcomma(str_wthrdat,2)          # We want the humidity which jst before the second comma
                        str_humidity = str_wthrdat[comma_no-4:comma_no] # We use the index number returned to extract the humidity
                        url_handle.close()
                        flag_url = True
                        if flag_debugging:
                                logger("%s: DEBUG weather access success", MYNAME)
                except:
                        # Something went wrong.  Force a retry on next tk_root.mainloop cycle.
                        if flag_debugging:
                                logger("%s: DEBUG Oops, weather access failed", MYNAME)
                        count_down = 0
                        flag_url = False
        count_down = count_down - 1
        now = time.localtime()
        str_date = time.strftime(FORMAT_DATE, now)
        str_time = time.strftime(FORMAT_TIME, now)
        if flag_debugging:
                logger("%s: DEBUG Display date = %s, time = %s, temp = %s F - %s %%",
                                MYNAME, str_date, str_time, str_temp, str_humidity)
#                print(flag_url)
#                print(parsed_json)

        return( str_date, str_time, str_temp, str_humidity )

# ----------------------------------------------------------
# Procedure: Main Loop
def display_main_procedure():
        if flag_debugging:
                logger("%s: DEBUG display_main_procedure begin", MYNAME)
        ( str_date, str_time, str_temp, str_humidity ) = get_display_data()
        display_date.config(text=str_date)
        display_time.config(text=str_time)
        if flag_url:
                display_cur_temp.config(fg=FG_COLOR_NORMAL)
                display_cur_cond.config(fg=FG_COLOR_NORMAL)
        else:
                display_cur_temp.config(fg=FG_COLOR_ABNORMAL)
                display_cur_cond.config(fg=FG_COLOR_ABNORMAL)
        display_cur_temp.config(text="%s F" % str_temp)
        display_cur_cond.config(text="%s %% " % str_humidity)
        if flag_debugging:
                logger("%s: DEBUG display_main_procedure going back to sleep", MYNAME)
        tk_root.after(SLEEP_TIME_MSEC, display_main_procedure)

# ----------------------------------------------------------
# Enter Tk mainloop
tk_root.after(0, display_main_procedure)
tk_root.bind('<ButtonPress>', talk_to_operator)
tk_root.mainloop()

logger("%s: tk_root left mainloop", MYNAME)

