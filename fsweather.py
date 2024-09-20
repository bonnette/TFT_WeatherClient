# https://api.open-meteo.com/v1/forecast?latitude=30.31188&longitude=-95.45605&current=temperature_2m,wind_speed_10m
import requests
import json
import time
import tkinter as tk

MYNAME = "home_weather"
flag_debugging = False
SLEEP_TIME_SEC = 300  # 5 minutes
SLEEP_TIME_MSEC = SLEEP_TIME_SEC * 1000  # milliseconds

URL_REQUEST_TIMEOUT_SEC = 60
COUNT_START = 0  # Fetch weather every 20th main loop execution
count_down = 0  # Fetch weather data from URL_LEFT when =0
flag_url = False
str_temp = "Network Error"
str_humidity = "Check Network"
str_wind = "0"
str_gust = "0"
str_press = "0"
str_dir = "None"
str_dirtxt = "None"

# Text display parameters

WINDOW_SIZE_ROOT = "480x320"
WINDOW_SIZE_POPUP = "320x200"
FONT_NAME = "helvetica"
FONT_SIZE = 40
SM_FONT_SIZE = 12
FONT_POPUP_SIZE = 24
FONT_STYLE = "bold"
SPACER_SIZE = 20
BUTTON_WIDTH = 6
BUTTON_HEIGHT = 2
FG_COLOR_NORMAL = "white"
FG_COLOR_WEATHER = "gold"
FG_COLOR_DATE = "steelblue"
FG_COLOR_ABNORMAL = "red"
BG_COLOR_ROOT = "black"
BG_COLOR_POPUP = BG_COLOR_ROOT
FORMAT_DATE = "%b %d, %Y"  # USA date format
FORMAT_TIME = "%I:%M %p %Z"  # Hours:Minutes + AM/PM for the USA

# ----------------------------------------------------------
# Wind Direction


def windconvert(numdir):
    if numdir >= 0 and numdir < 22:
        direction = "North"
        return direction
    elif numdir >= 22 and numdir < 45:
        direction = "NNE"
        return direction
    elif numdir >= 45 and numdir < 67:
        direction = "NE"
        return direction
    elif numdir >= 67 and numdir < 90:
        direction = "ENE"
        return direction
    elif numdir >= 90 and numdir < 112:
        direction = "East"
        return direction
    elif numdir >= 112 and numdir < 135:
        direction = "ESE"
        return direction
    elif numdir >= 135 and numdir < 157:
        direction = "SE"
        return direction
    elif numdir >= 157 and numdir < 180:
        direction = "SSE"
        return direction
    elif numdir >= 180 and numdir < 202:
        direction = "South"
        return direction
    elif numdir >= 202 and numdir < 225:
        direction = "SSW"
        return direction
    elif numdir >= 225 and numdir < 247:
        direction = "SW"
        return direction
    elif numdir >= 247 and numdir < 270:
        direction = "WSW"
        return direction
    elif numdir >= 270 and numdir < 292:
        direction = "West"
        return direction
    elif numdir >= 292 and numdir < 315:
        direction = "WNW"
        return direction
    elif numdir >= 315 and numdir < 337:
        direction = "NW"
        return direction
    elif numdir >= 337 and numdir < 359:
        direction = "NNW"
        return direction
    else:
        return "None"


# -------------------------------------------------------------------


# Initialize Tk

tk_root = tk.Tk()
tk_root.attributes("-fullscreen", True)
# set BG color and turn off cursor
tk_root.configure(background=BG_COLOR_ROOT, cursor="none")
tk_root.geometry(WINDOW_SIZE_ROOT)

# display_spacer1 = Label(tk_root, font=(FONT_NAME, SPACER_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL,bg=BG_COLOR_ROOT)
# display_spacer1.pack()
# display_spacer1.config(text=" ")

# ----------------------------------------------------------

# Build display lines

display_date = tk.Label(
    tk_root,
    font=(FONT_NAME, SM_FONT_SIZE, FONT_STYLE),
    fg=FG_COLOR_DATE,
    bg=BG_COLOR_ROOT,
)
display_date.pack()

display_time = tk.Label(
    tk_root, font=(FONT_NAME, FONT_SIZE, FONT_STYLE), fg=FG_COLOR_DATE, bg=BG_COLOR_ROOT
)
display_time.pack()

display_cur_temp = tk.Label(
    tk_root,
    font=(FONT_NAME, FONT_SIZE, FONT_STYLE),
    fg=FG_COLOR_WEATHER,
    bg=BG_COLOR_ROOT,
)
display_cur_temp.pack()

display_cur_wind = tk.Label(
    tk_root,
    font=(FONT_NAME, FONT_SIZE, FONT_STYLE),
    fg=FG_COLOR_WEATHER,
    bg=BG_COLOR_ROOT,
)
display_cur_wind.pack()

display_cur_pressure = tk.Label(
    tk_root,
    font=(FONT_NAME, FONT_SIZE, FONT_STYLE),
    fg=FG_COLOR_WEATHER,
    bg=BG_COLOR_ROOT,
)
display_cur_pressure.pack()

# display_spacer2 = Label(tk_root, font=(FONT_NAME, SPACER_SIZE, FONT_STYLE), fg=FG_COLOR_NORMAL, bg=BG_COLOR_ROOT)
# display_spacer2.pack()
# display_spacer2.config(text=" ")

# ----------------------------------------------------------

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below


def get_display_data():
    global count_down, str_temp, str_humidity, flag_url

    # if count_down < 1:
    # Time to go geat new weather data
    #  count_down = COUNT_START

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 30.311876,
        "longitude": -95.456055,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "surface_pressure",
        ],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/Chicago",
    }

    # Pull current weather from web decode the response and put it in "data"
    try:
        response = requests.get(url, params=params)
        data = response.json()

        # Uncomment below to see everything returned from the Open-Meteo.com server
        # print(data)

        # Current values. The order of variables needs to be the same as requested.

        str_temp = data["current"]["temperature_2m"]
        str_humidity = data["current"]["relative_humidity_2m"]
        str_wind = data["current"]["wind_speed_10m"]
        wind_direction = data["current"]["wind_direction_10m"]
        str_gust = data["current"]["wind_gusts_10m"]
        current_pressure = data["current"]["surface_pressure"]

        # Convert numerical wind direction into text (north, South etc)
        str_dirtxt = windconvert(wind_direction)

        # convert barometric pressure in milibars to inches round out
        # the number and limit the places after the decimal point to 2
        str_press = round((current_pressure * 0.02953), 2)

        # If we are at this point with no issues then the weather was
        # succfully recieved from the website so set the flag to True
        flag_url = True
    except:
        # Something went wrong.  Force a retry on next tk_root.mainloop cycle.

        # count_down = 0
        flag_url = False

    # count_down = count_down - 1
    now = time.localtime()
    str_date = time.strftime(FORMAT_DATE, now)
    str_time = time.strftime(FORMAT_TIME, now)
    str_time = str_time.lstrip("0")  # Get rid of leading zero

    return (
        str_date,
        str_time,
        str_temp,
        str_humidity,
        str_wind,
        str_dirtxt,
        str_press,
        str_gust,
    )


# -------------------------------------------------------------------------------------------------------------
# Procedure: Main Loop


def display_main_procedure():

    (
        str_date,
        str_time,
        str_temp,
        str_humidity,
        str_wind,
        str_dirtxt,
        str_press,
        str_gust,
    ) = get_display_data()
    display_date.config(text=str_date)
    display_time.config(text=str_time)
    # Check if weather is from website if not make the Temp and Humidity Red
    if flag_url:
        display_cur_temp.config(fg=FG_COLOR_WEATHER)
    else:
        display_cur_temp.config(fg=FG_COLOR_ABNORMAL)
    display_cur_temp.config(text="%s F - %s %%" % (str_temp, str_humidity))
    display_cur_wind.config(text="%s - %s Mph" % (str_dirtxt, str_wind))
    display_cur_pressure.config(text="Gust %s - %s" % (str_gust, str_press))

    tk_root.after(SLEEP_TIME_MSEC, display_main_procedure)


# ----------------------------------------------------------
# Enter Tk mainloop

tk_root.after(0, display_main_procedure)

tk_root.mainloop()

# ( str_date, str_time, str_temp, str_humidity, str_wind, str_dirtxt, str_press, str_gust ) = get_display_data()

# display_cur_temp.config(text="%s F - %s %%" % (str_temp, str_humidity))
