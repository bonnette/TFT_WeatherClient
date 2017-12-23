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
# We extract the data starting from the "wthrdata.dat" file counting the commas. The data before the first comma 1 = Outside Temperature 'C'
# comma 2 = Humidity, 3 = Indoor temp 'C', 4 = Barometric pressure hpa, 5 = Altitude k, 6 = current wind speed kph, 7 = wind gust kph, 8 = rain total, ........16 = Date and Time
##--------------------------------------------------------------

import os, time, sys, subprocess, json

MYNAME = 'home_weather'
flag_debugging = False
SLEEP_TIME_SEC = 60
SLEEP_TIME_MSEC = SLEEP_TIME_SEC*1000 # milliseconds

# ----------------------------------------------------------
# Weather station url info

FULL_URL = 'http://192.168.0.196/wthrdata.dat' # set up url for wthrdata.dat
URL_REQUEST_TIMEOUT_SEC = 60
COUNT_START = 0 # Fetch weather every 20th main loop execution
count_down = 0 # Fetch weather data from URL_LEFT when =0
flag_url = False
str_temp = 'Network Error'
str_humidity = 'Check Network'
str_wind = '0'
str_dir = 'None'
str_dirtxt = 'None'
comma_no = 0

# ----------------------------------------------------------
# Video display parameters

WINDOW_SIZE_ROOT = "480x320"
WINDOW_SIZE_POPUP = "320x200"
FONT_NAME = 'helvetica'
FONT_SIZE = 40
SM_FONT_SIZE = 12
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

#------------------------------------------------------------------
# Wind Direction

def windconvert(numdir):
    if numdir >= 0 and numdir < 22:
        direction = 'North'     
        return direction
    elif numdir >= 22 and numdir < 45:
        direction = 'NNE'
        return direction
    elif numdir >= 45 and numdir < 67:
        direction = 'NE'
        return direction
    elif numdir >= 67 and numdir < 90:
        direction = 'ENE'
        return direction
    elif numdir >= 90 and numdir < 112:
        direction = 'East'
        return direction
    elif numdir >= 112 and numdir < 135:
        direction = 'ESE'
        return direction
    elif numdir >= 135 and numdir < 157:
        direction = 'SE'
        return direction
    elif numdir >= 157 and numdir < 180:
        direction = 'SSE'
        return direction
    elif numdir >= 180 and numdir < 202:
        direction = 'South'
        return direction
    elif numdir >= 202 and numdir < 225:
        direction = 'SSW'
        return direction
    elif numdir >= 225 and numdir < 247:
        direction = 'SW'
        return direction
    elif numdir >= 247 and numdir < 270:
        direction = 'WSW'
        return direction
    elif numdir >= 270 and numdir < 292:
        direction = 'West'
        return direction
    elif numdir >= 292 and numdir < 315:
        direction = 'WNW'
        return direction
    elif numdir >= 315 and numdir < 337:
        direction = 'NW'
        return direction
    elif numdir >= 337 and numdir < 359:
        direction = 'NNW'
        return direction
    else:
        return 'None'


#-------------------------------------------------------------------
# comma index function
# returns the index number of a comma
# "needle" defines the charater we want to find. "haystack" is the text we will search through.
# "n" is the number of commas we want to find. "start" holds the index number for the text we want to return back to the program.
# Example: Indoor Temp is the third comma into the data. So if we want to get the indoor temp data n will = 3

def getcomma(haystack,n):
        needle = ','
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start

#------------------------------------------------------------------
# Exit procedure initiated by Exit Button

def proc_exitr():

        sys.exit()

#------------------------------------------------------------------
def proc_shutdown():

        if flag_debugging:
                logger("%s: DEBUG proc_shutdown begin", MYNAME)
        args = ['sudo', 'shutdown', 'now']
        cp = subprocess.run(args, stdout=subprocess.PIPE)

#-------------------------------------------------------------------
# Exit button popup window

def talk_to_operator(event):
        if flag_debugging:
                logger("%s: DEBUG talk_to_operator begin", MYNAME)
        tk_popup = Tk()
        tk_popup.title("Exit App")
        tk_popup.attributes("-fullscreen", False)
        tk_popup.configure(background=BG_COLOR_POPUP)
        tk_popup.geometry(WINDOW_SIZE_POPUP)
# Go Back Button
        b_goback = Button(tk_popup, text="Go Back", command=tk_popup.destroy,
                 font=(FONT_NAME, FONT_POPUP_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL)
        b_goback.focus_set()
        b_goback.pack(fill="both", expand=True)

# Exit to OS button
        b_exitr = Button(tk_popup, text='Exit', command=proc_exitr,
                                        font=(FONT_NAME, FONT_POPUP_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL)
        b_exitr.pack(fill="both", expand=True)

# Shutdown Pi button (necessary to prevent corruption)
        b_shutdown = Button(tk_popup, text='Shutdown', command=proc_shutdown,
                                        font=(FONT_NAME, FONT_POPUP_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL)
        b_shutdown.pack(fill="both", expand=True)

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

display_date = Label(tk_root, font=(FONT_NAME, SM_FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_date.pack()

display_time = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_time.pack()

display_cur_temp = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_cur_temp.pack()

display_cur_humidity = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_cur_humidity.pack()

display_cur_wind = Label(tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
display_cur_wind.pack()

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
                        data = url_handle.read()                    # gets the weather data from weather station
                        encoding = url_handle.info().get_content_charset('utf-8')
                        parsed_json = json.loads(data.decode(encoding))
                        str_wthrdat = parsed_json['FullDataString'] # places weather data into variable
                        comma_no = getcomma(str_wthrdat,1)          # We want the outdoor temperature which is just before the first comma.
                        str_temp = str_wthrdat[comma_no-4:comma_no] # We use the index number returned to extract the outdoor temperature
                        str_temp = ('%.1f' % ((float(str_temp) * 1.8) + 32)) # Convert "C" to Farenheite
                        comma_no = getcomma(str_wthrdat,2)          # We want the humidity which is just before the second comma
                        str_humidity = str_wthrdat[comma_no-4:comma_no] # We use the index number returned to extract the humidity
                        comma_no = getcomma(str_wthrdat,6)          # We want the wind speed which is just before the 6th comma
                        str_wind = str_wthrdat[comma_no-4:comma_no] # We use the index number returned to extract the speed
                        comma_no = getcomma(str_wthrdat,8)          # We want the wind direction which is just before the 8th comma
                        str_dir = str_wthrdat[comma_no-5:comma_no] # We use the index number returned to extract the dir
                        str_dirtxt = windconvert(float(str_dir))
                        str_wind = str_wind.lstrip('0') # get rid of leading zero
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
        str_time = str_time.lstrip('0') # Get rid of leading zero
        if flag_debugging:
                logger("%s: DEBUG Display date = %s, time = %s, temp = %s F humidity = %s %% Speed = %s mph Dir = %s ",
                                MYNAME, str_date, str_time, str_temp, str_humidity, str_wind, str_dirtxt)
#                print(flag_url)
#                print(parsed_json)
        return( str_date, str_time, str_temp, str_humidity, str_wind, str_dirtxt )

# ----------------------------------------------------------
# Procedure: Main Loop

def display_main_procedure():
        if flag_debugging:
                logger("%s: DEBUG display_main_procedure begin", MYNAME)
        ( str_date, str_time, str_temp, str_humidity, str_wind, str_dirtxt ) = get_display_data()
        display_date.config(text=str_date)
        display_time.config(text=str_time)
        if flag_url:
                display_cur_temp.config(fg=FG_COLOR_NORMAL)
                display_cur_humidity.config(fg=FG_COLOR_NORMAL)
        else:
                display_cur_temp.config(fg=FG_COLOR_ABNORMAL)
                display_cur_humidity.config(fg=FG_COLOR_ABNORMAL)
        display_cur_temp.config(text="%s F" % str_temp)
        display_cur_humidity.config(text="%s %% " % str_humidity)
        display_cur_wind.config(text="%s - %s Mph" % (str_dirtxt, str_wind))
        if flag_debugging:
                logger("%s: DEBUG display_main_procedure going back to sleep", MYNAME)
        tk_root.after(SLEEP_TIME_MSEC, display_main_procedure)

# ----------------------------------------------------------
# Enter Tk mainloop

tk_root.after(0, display_main_procedure)
tk_root.bind('<ButtonPress>', talk_to_operator)
tk_root.mainloop()

logger("%s: tk_root left mainloop", MYNAME)

