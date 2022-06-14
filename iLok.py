#!/usr/bin/env python

import os
import sys
import subprocess
import traceback
import getpass
import time
import tempfile

# https://github.com/picklepete/pyicloud
# python -m pip install --user pyicloud
try:
  from pyicloud import PyiCloudService
except:
  traceback.print_exc()
  subprocess.run([
    sys.executable,
    *('-m pip install --user pyicloud'.split(' '))
  ])
  from pyicloud import PyiCloudService

# python -m pip install --user click
try:
  import click
except:
  traceback.print_exc()
  subprocess.run([
    sys.executable,
    *('-m pip install --user click'.split(' '))
  ])
  import click

# python -m pip install --user staticmap
try:
  import staticmap
except:
  traceback.print_exc()
  subprocess.run([
    sys.executable,
    *('-m pip install --user staticmap'.split(' '))
  ])
  import staticmap


# Comcast's v6 SUCKS, change stdlib to ignore it
import socket
import requests.packages.urllib3.util.connection as urllib3_cn

def allowed_gai_family():
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET
    return family

urllib3_cn.allowed_gai_family = allowed_gai_family


def handle_auth(api):
  if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
      print("Failed to verify security code")
      sys.exit(1)

    if not api.is_trusted_session:
      print("Session is not trusted. Requesting trust...")
      result = api.trust_session()
      print("Session trust result %s" % result)

      if not result:
        print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")

  elif api.requires_2sa:
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
      print("  %s: %s" % (i, device.get('deviceName',
          "SMS to %s" % device.get('phoneNumber'))))

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
      print("Failed to send verification code")
      sys.exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
      print("Failed to verify verification code")
      sys.exit(1)

def get_device(devices, name):
  for d in devices:
    if name in str(d):
      return d
  return None


def main():
  
  # profile_img must be smaller than 512x512 px (size of map)
  profile_img = '/j/photos/profiles/basic-1x1-tiny.png'
  profile_img_size_px = (128, 128)

  map_img = os.path.join(tempfile.gettempdir(), 'iLok.png')

  print(f'Your map profile picture will be read from {profile_img} ')
  print(f'Your map image will be written to {map_img} ')
  
  appleid = os.environ.get('APPLE_ID', None) or getpass.getpass('Apple ID: ').strip()
  pw = ''
  cookie_directory = os.path.join(tempfile.gettempdir(), 'idevices_cookies')
  os.makedirs(cookie_directory, exist_ok=True)
  print(f'Storing idevice cookies in {cookie_directory}')

  api = None
  try:
    api = PyiCloudService(appleid, pw, cookie_directory=cookie_directory)
    __ignored = get_device(api.devices, 'iPhone')
  except Exception as e:
    traceback.print_exc()
    pw = os.environ.get('APPLE_PW', None) or getpass.getpass('Apple Password: ').strip()
    api = PyiCloudService(appleid, pw, cookie_directory=cookie_directory)

  handle_auth(api)
  print(f'api={api}')

  my_phone = get_device(api.devices, 'iPhone') # text is arbitrary search
  print(f'my_phone={my_phone}')

  input('Press enter to begin tracking!')

  the_map = staticmap.StaticMap(1224, 960, url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')

  while True:

    l = my_phone.location()
    #print(f'I am at {l}')
    lat = l.get('latitude', 0.0)
    lon = l.get('longitude', 0.0)

    the_map.markers = [
      staticmap.IconMarker((lon, lat), profile_img, int(profile_img_size_px[0] / 2), int(profile_img_size_px[1] / 2) )
    ]

    img = the_map.render(zoom=12, center=(lon, lat))
    img.save(map_img)

    # Rapid Debugging, replace feh w/ image viewer of choice
    # subprocess.run(['feh', map_img])

    print(f'I am at {lat}, {lon} and a map is rendered at {map_img}')
    time.sleep(2.0)








if __name__ == '__main__':
  main()


