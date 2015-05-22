drumminhands_photobooth
=======================

A DIY photo booth using a Raspberry Pi that automatically sends images to a Flickr account. Great for events.

Find the full set of instructions here for tumblr version: http://www.drumminhands.com/2014/06/15/raspberry-pi-photo-booth/
This requires:
  - PiCamera -- http://picamera.readthedocs.org/
  - GraphicsMagick -- http://www.graphicsmagick.org/ (This is optional)
  - flickrapi - http://stuvel.eu/media/flickrapi-docs/documentation/
  
Quick set instructions:

0) Wire the button and LED. Check the wiring by running testcircuit.py

1) Use the GUI interface, but open the terminal program. Update the config.py file with your api_key and api_secret. The api_key and api_secret can be obtained from http://www.flickr.com/services/api/keys/

2) Run auth.py

3) It will open a browser window and ask you to authorize on yahoo/flickr. Go ahead and authorize. The result will be a page with a number. Type that number into the terminal session and press enter.

4) Check that the test image was uploaded to your Flickr site

5) Run drumminhands_piFlickr.py. Consider making this autostart when the Raspberry Pi starts up.
