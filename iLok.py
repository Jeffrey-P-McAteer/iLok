#!/usr/bin/env python

import os
import sys
import subprocess
import traceback
import getpass
import time

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
  appleid = 'jeffrey.p.mcateer@gmail.com'
  pw = ''
  cookie_directory = '/tmp/idevices_cookies/'
  os.makedirs(cookie_directory, exist_ok=True)
  
  api = None
  try:
    api = PyiCloudService(appleid, pw, cookie_directory=cookie_directory)
    __ignored = get_device(api.devices, 'iPhone 12 Pro')
  except Exception as e:
    print(e)
    pw = os.environ.get('APPLE_PW', None) or getpass.getpass('Apple Password: ').strip()
    api = PyiCloudService(appleid, pw, cookie_directory=cookie_directory)

  handle_auth(api)
  print(f'api={api}')

  my_phone = get_device(api.devices, 'iPhone') # text is arbitrary search
  print(f'my_phone={my_phone}')

  while True:
    time.sleep(1.0)

    l = my_phone.location()
    #print(f'I am at {l}')
    lat = l.get('latitude', 0.0)
    lon = l.get('longitude', 0.0)

    print(f'I am at {lat}, {lon}')






if __name__ == '__main__':
  main()


