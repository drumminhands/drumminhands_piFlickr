#!/usr/bin/env python

import config
import flickrapi
import webbrowser

fileToUpload = '/home/pi/photobooth/slides/test_upload.png' #change to a real filename

tagsToTag = 'photobooth testing'

def toUnicodeOrBust(obj, encoding='utf-8'):
  if isinstance(obj, basestring):
    if not isinstance(obj, unicode):
      obj = unicode(obj, encoding)
  return obj

flickr = flickrapi.FlickrAPI(config.api_key, config.api_secret)

print('Step 1: authenticate')

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms=u'write'): #notice the letter u. It's important.

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms=u'write') #notice the letter u. It's important.
    webbrowser.open_new_tab(authorize_url)

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = toUnicodeOrBust(raw_input('Verifier code: '))

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

#print('Step 2: use Flickr')
flickr.upload(filename=fileToUpload, tags=tagsToTag)