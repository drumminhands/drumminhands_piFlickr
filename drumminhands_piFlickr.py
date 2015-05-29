#!/usr/bin/env python
# created by chris@drumminhands.com
# see instructions at http://www.drumminhands.com/2015/05/22/raspberry-pi-and-flickr/

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
from signal import alarm, signal, SIGALRM, SIGKILL

########################
### Variables Config ###
########################
ledPin = 11 # LED 1
btnPin1 = 37 # pin for the big red button
btnPin2 = 18 # pin for button to shutdown the pi
btnPin3 = 22 # pin for button to end the program, but not shutdown the pi

prepDelay = 1 # number of seconds at step 1 as users prep to have photo taken
replayDelay = 2 # how long to show the image before uploading to flickr?
doneDelay = 6 # how long to hold the done screen before restarting the process

testServer = 'www.google.com'
realPath = os.path.dirname(os.path.realpath(__file__))

tagsToTag = 'photobooth testing'

monitorWidth = 1392;
monitorHeight = 868;

offsetX = 0 # how far off to left corner to display photos
offsetY = 0 # how far off to left corner to display photos

####################
### Other Config ###
####################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledPin,GPIO.OUT) # LED 1
GPIO.setup(btnPin1, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 1
GPIO.setup(btnPin2, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 2
GPIO.setup(btnPin3, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 3

#################
### Functions ###
#################

def cleanup():
	print('Ended abruptly')
	GPIO.cleanup()
atexit.register(cleanup)

def shutItDown(channel):  
	print "Shutting down..." 
	GPIO.output(ledPin,True);
	time.sleep(3)
	os.system("sudo halt")

def exitApp(channel):
    print "Photo booth app ended. RPi still running" 
    GPIO.output(ledPin,True);
    time.sleep(3)
    sys.exit()
         
def isConnected():
	try:
		# see if we can resolve the host name -- tells us if there is a DNS listening
		host = socket.gethostbyname(testServer)
		# connect to the host -- tells us if the host is actually reachable
		s = socket.create_connection((host, 80), 2)
		return True
	except:
		 pass
	return False    

def initPygame():
    pygame.init()
    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    pygame.display.set_caption('Photo Booth Pics')
    pygame.mouse.set_visible(False) #hide the mouse cursor	
    return pygame.display.set_mode(size, pygame.FULLSCREEN)

def showImage(imagePath):
    screen = initPygame()
    img=pygame.image.load(imagePath) 
    img = pygame.transform.scale(img,(monitorWidth,monitorHeight))
    screen.blit(img,(offsetX,offsetY))
    pygame.display.flip()

def toUnicodeOrBust(obj, encoding='utf-8'):
	  if isinstance(obj, basestring):
		if not isinstance(obj, unicode):
			obj = unicode(obj, encoding)
	  return obj

def waitForBtn(t=0):
	sleep(t)#wait a minimum of this many seconds
	GPIO.output(ledPin,True) #turn the light on
	while True: #wait for a button press
		GPIO.wait_for_edge(btnPin1, GPIO.FALLING)
		time.sleep(0.2) #debounce
		break

def uploadToFlickr(file,tag):
	connected = isConnected() #check to see if you have an internet connection
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
			flickr.upload(filename=file, tags=tag)
			break
		except ValueError:
			print "Oops. No internect connection. Upload later."
			try: #make a text file as a note to upload the .gif later
				file = open(config.file_path + f + "-FILENOTUPLOADED.txt",'w')   # Trying to create a new file or open one
				file.close()
			except:
				print('Something went wrong. Could not write file.')
			sys.exit(0) # quit Python


# define the photo taking function for when the button is pressed 
def startApp():   
        
	#show the instructions
	GPIO.output(ledPin,False) #turn the light off
	showImage(realPath + "/slides/intro.png")
	waitForBtn(prepDelay)
        
	#get ready to take pics
	showImage(realPath + "/slides/blank.png")
	GPIO.output(ledPin,False) #turn the light off
	with picamera.PiCamera() as camera: #use the 'with' for faster image taking
		camera.resolution = (monitorWidth, monitorHeight)
		camera.framerate = 30 #adjusting the framerate affects the preview image quality. Careful.
		camera.vflip = True
		camera.hflip = False
		camera.start_preview()
		time.sleep(1) #Let the camera warm up

		#iterate the blink of the light in prep, also gives a little time for the camera to warm up
		GPIO.output(ledPin,True); sleep(.25) 
		GPIO.output(ledPin,False); sleep(.25)
		GPIO.output(ledPin,True); sleep(.25)

		waitForBtn(0) #wait for a button press
	    
		#take one picture 
		now = time.strftime("%Y-%m-%d-%H_%M_%S") #get the current date and time for the start of the filename
		fileToUpload = config.file_path + now + '.jpg'
		try: #take the photos                
			GPIO.output(ledPin,False) #turn off the LED
			camera.capture(fileToUpload);
		finally:
			camera.stop_preview()				
			camera.close()
	
	#show the image
	showImage(fileToUpload) #show the one image until flickr upload complete
	time.sleep(replayDelay) #pause for a minimum amount of time
	
	#upload to flickr
	uploadToFlickr(fileToUpload,tagsToTag)
	
	#display final screen
	showImage(realPath + "/slides/done.png");
	time.sleep(doneDelay)

	#start over
	GPIO.output(ledPin,True) #turn on the LED
	showImage(realPath + "/slides/attract.png");

####################
### Main Program ###
####################

# when a falling edge is detected on btnPin2 and btnPin3, regardless of whatever   
# else is happening in the program, their function will be run   
GPIO.add_event_detect(btnPin2, GPIO.FALLING, callback=shutItDown, bouncetime=300) 

#choose one of the two following lines to be un-commented
GPIO.add_event_detect(btnPin3, GPIO.FALLING, callback=exitApp, bouncetime=300) #use third button to exit python. Good while developing
#GPIO.add_event_detect(btnPin3, GPIO.FALLING, callback=clear_pics, bouncetime=300) #use the third button to clear pics stored on the SD card from previous events

# delete files in folder on startup
files = glob.glob(config.file_path + '*')
for f in files:
    os.remove(f)

print "Photo booth app running..." 
#light up the lights to show the app is running
j = 1
while j<4:
	GPIO.output(ledPin,False);
	time.sleep(0.25) 
	GPIO.output(ledPin,True);
	time.sleep(0.25)
	j+=1

showImage(realPath + "/slides/attract.png");

while True:
	GPIO.wait_for_edge(btnPin1, GPIO.FALLING)
	time.sleep(0.2) #debounce
	startApp()
