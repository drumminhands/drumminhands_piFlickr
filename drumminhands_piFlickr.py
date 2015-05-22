#!/usr/bin/env python
# created by chris@drumminhands.com
# see instructions for tumblr version at http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/

import os
import glob
import time
import traceback
from time import sleep
import RPi.GPIO as GPIO
import picamera
import atexit
import sys
import socket
import pygame
import config
import flickrapi
import webbrowser

########################
### Variables Config ###
########################
led_pin = 11 # LED 1
button1_pin = 37 # pin for the big red button
button2_pin = 18 # pin for button to shutdown the pi
button3_pin = 16 # pin for button to end the program, but not shutdown the pi

total_pics = 1 # number of pics  to be taken
capture_delay = 0 # delay between pics
prep_delay = 3 # number of seconds at step 1 as users prep to have photo taken
gif_delay = 50 # How much time between frames in the animated gif

test_server = 'www.google.com'
real_path = os.path.dirname(os.path.realpath(__file__))

tagsToTag = 'photobooth testing'

transform_x = 1872 # how wide to scale the jpg when replaying
transfrom_y = 1168 # how high to scale the jpg when replaying
offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos
replay_delay = 1 # how much to wait in-between showing pics on-screen after taking
replay_cycles = 1 # how many times to show each photo on-screen after taking

####################
### Other Config ###
####################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin,GPIO.OUT) # LED 1
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 1
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 2
GPIO.setup(button3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 3

#################
### Functions ###
#################

def cleanup():
  print('Ended abruptly')
  GPIO.cleanup()
atexit.register(cleanup)

def shut_it_down(channel):  
    print "Shutting down..." 
    GPIO.output(led_pin,True);
    time.sleep(3)
    os.system("sudo halt")

def exit_photobooth(channel):
    print "Photo booth app ended. RPi still running" 
    GPIO.output(led_pin,True);
    time.sleep(3)
    sys.exit()
    
def clear_pics(foo): #why is this function being passed an arguments?
    #delete files in folder on startup
	files = glob.glob(config.file_path + '*')
	for f in files:
		os.remove(f) 
	#light the lights in series to show completed
	print "Deleted previous pics"
	GPIO.output(led_pin,True); 
	sleep(0.25)
	GPIO.output(led_pin,False);
	sleep(0.25)
      
def is_connected():
  try:
    # see if we can resolve the host name -- tells us if there is a DNS listening
    host = socket.gethostbyname(test_server)
    # connect to the host -- tells us if the host is actually reachable
    s = socket.create_connection((host, 80), 2)
    return True
  except:
     pass
  return False    

def init_pygame():
    pygame.init()
    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    pygame.display.set_caption('Photo Booth Pics')
    pygame.mouse.set_visible(False) #hide the mouse cursor	
    return pygame.display.set_mode(size, pygame.FULLSCREEN)

def show_image(image_path):
    screen = init_pygame()
    img=pygame.image.load(image_path) 
    img = pygame.transform.scale(img,(transform_x,transfrom_y))
    screen.blit(img,(offset_x,offset_y))
    pygame.display.flip()

def display_pics(jpg_group):
    # this section is an unbelievable nasty hack - for some reason Pygame
    # needs a keyboardinterrupt to initialise in some limited circs (second time running)

    class Alarm(Exception):
        pass
    def alarm_handler(signum, frame):
        raise Alarm
    signal(SIGALRM, alarm_handler)
    alarm(3)
    try:
        screen = init_pygame()

        alarm(0)
    except Alarm:
        raise KeyboardInterrupt
    for i in range(0, replay_cycles): #show pics a few times
		for i in range(1, total_pics+1): #show each pic
			filename = config.file_path + jpg_group + ".jpg"
                        show_image(filename);
			time.sleep(replay_delay) # pause 

def toUnicodeOrBust(obj, encoding='utf-8'):
  if isinstance(obj, basestring):
    if not isinstance(obj, unicode):
      obj = unicode(obj, encoding)
  return obj

# define the photo taking function for when the big button is pressed 
def start_photobooth(): 
	################################# Begin Step 1 ################################# 
	print "Get Ready" 
        show_image(real_path + "/slides/intro.png")
        sleep(4)#display intro message for this many seconds
	show_image(real_path + "/slides/blank.png")

	camera = picamera.PiCamera()
	#camera.resolution = (640, 480) #use a smaller size to process faster, and tumblr will only take up to 500 pixels wide for animated gifs
	camera.vflip = False
	camera.hflip = False
	#camera.saturation = -100
	camera.start_preview()

	#iterate the blink of the light in prep, also gives a little time for the camera to warm up
	GPIO.output(led_pin,True); sleep(.5) 
	GPIO.output(led_pin,False); sleep(.5)
        GPIO.output(led_pin,True); sleep(.5)

	while True: #wait for another button press
        	GPIO.wait_for_edge(button1_pin, GPIO.FALLING)
		time.sleep(0.2) #debounce
		break
	################################# Begin Step 2 #################################
	print "Taking pics" 
	now = time.strftime("%Y-%m-%d-%H_%M_%S") #get the current date and time for the start of the filename
        fileToUpload = config.file_path + now + '.jpg'
	try: #take the photos
                camera.capture(fileToUpload);
		GPIO.output(led_pin,False) #turn off the LED
		print(fileToUpload)
		sleep(capture_delay) # pause in-between shots
	finally:		
		camera.stop_preview()
		camera.close()
	########################### Begin Step 3 #################################
        show_image(real_path + "/slides/uploading.png")

	print "Uploading to Flickr."

	connected = is_connected() #check to see if you have an internet connection
	while connected: 
		try:
			flickr = flickrapi.FlickrAPI(config.api_key, config.api_secret)

			print('Step 1: authenticate')

			# Only do this if we don't have a valid token already
			if not flickr.token_valid(perms=u'write'):

				# Get a request token
				flickr.get_request_token(oauth_callback='oob')

				# Open a browser at the authentication URL. Do this however
				# you want, as long as the user visits that URL.
				authorize_url = flickr.auth_url(perms=u'write')
				webbrowser.open_new_tab(authorize_url)

				# Get the verifier code from the user. Do this however you
				# want, as long as the user gives the application the code.
				verifier = toUnicodeOrBust(raw_input('Verifier code: '))

				# Trade the request token for an access token
				flickr.get_access_token(verifier)
			flickr.upload(filename=fileToUpload, tags=tagsToTag)
			break
		except ValueError:
			print "Oops. No internect connection. Upload later."
			try: #make a text file as a note to upload the .gif later
				file = open(config.file_path + now + "-FILENOTUPLOADED.txt",'w')   # Trying to create a new file or open one
				file.close()
			except:
				print('Something went wrong. Could not write file.')
				sys.exit(0) # quit Python
	########################### Begin Step 4 #################################	
	try:
		display_pics(now)
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)
	pygame.quit()
	print "Done"
	GPIO.output(led_pin,True) #turn on the LED
        show_image(real_path + "/slides/done.png");
        time.sleep(5)
        show_image(real_path + "/slides/attract.png");

####################
### Main Program ###
####################

# when a falling edge is detected on button2_pin and button3_pin, regardless of whatever   
# else is happening in the program, their function will be run   
GPIO.add_event_detect(button2_pin, GPIO.FALLING, callback=shut_it_down, bouncetime=300) 

#choose one of the two following lines to be un-commented
GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=exit_photobooth, bouncetime=300) #use third button to exit python. Good while developing
#GPIO.add_event_detect(button3_pin, GPIO.FALLING, callback=clear_pics, bouncetime=300) #use the third button to clear pics stored on the SD card from previous events

# delete files in folder on startup
files = glob.glob(config.file_path + '*')
for f in files:
    os.remove(f)

print "Photo booth app running..." 
#light up the lights to show the app is running
j = 1
while j<4:
  GPIO.output(led_pin,False);
  time.sleep(0.25) 
  GPIO.output(led_pin,True);
  time.sleep(0.25)
  j+=1

show_image(real_path + "/slides/attract.png");

while True:
        GPIO.wait_for_edge(button1_pin, GPIO.FALLING)
	time.sleep(0.2) #debounce
	start_photobooth()
