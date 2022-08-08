"""
Sample program to show the ISS in an AR view
"""

import board
import busio
from time import sleep
from math import atan2, copysign, asin, pi, degrees
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ACCELEROMETER, BNO_REPORT_ROTATION_VECTOR

from tkinter import *
from PIL import Image, ImageTk
import cv2

i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)
bno = BNO08X_I2C(i2c)
# bno.enable_feature(BNO_REPORT_ACCELEROMETER)
bno.enable_feature(BNO_REPORT_ROTATION_VECTOR)

win = Tk()
win.geometry('700x350')
label = Label(win)
label.grid(row=0, column=0)
cap = cv2.VideoCapture(0)

CAM_H = 62.2  # horizontal FOV for the raspberry pi camera module v2
CAM_V = 48.8  # vertical FOV


device_pos = {
    'roll' = 0,  # equivalent to altitude
    'pitch' = 0,
    'yaw' = 0  # equivalent to azimuth
}

sat_pos = {
    'altitude' = 0,
    'azimuth' = 0
}

def drawSat(device_pos, sat_pos, CAM_H, CAM_V):
    max_delta_h = CAM_H / 2
    max_delta_V = CAM_V / 2
    # get altitude delta
    
    # get azimuth delta
    
    # account for device pitch


def quatToEuler(x, y, z, w):
    # roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if (abs(sinp) >= 1):
        pitch = copysign(pi / 2, sinp) # use 90 degrees if out of range
    else:
        pitch = asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

# Define function to show frame
def show_frames():
   # Get the latest frame and convert into Image
   cv2image= cv2.cvtColor(cap.read()[1],cv2.COLOR_BGR2RGB)
   img = Image.fromarray(cv2image)
   # Convert image to PhotoImage
   imgtk = ImageTk.PhotoImage(image = img)
   label.imgtk = imgtk
   label.configure(image=imgtk)
   # Repeat after an interval to capture continiously
   label.after(20, show_frames)

show_frames()
win.mainloop()
    