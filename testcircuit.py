#!/usr/bin/env python

# use this to test if you wired the button correctly.

import RPi.GPIO as GPIO
from time import sleep

led_pin = 11      # LED pin
button_pin = 37   # button pin
delay = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin,GPIO.OUT)
GPIO.setup(button_pin,GPIO.IN)

i = 1
while i < 4:
  if GPIO.input(button_pin):
    GPIO.output(led_pin,False)
    print('Button pushed: ' + str(i))
    sleep(delay)
    i+=1
  else:
    GPIO.output(led_pin,True)

GPIO.cleanup()
