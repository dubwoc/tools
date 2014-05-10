#!/usr/bin/python3

import os
import signal
import requests
import subprocess
import datetime
import time


"""
Quick and dirty way to crawl through a number of OpenVPN configs
and test for speed.
"""
# Path to *.ovpn files.
VPN_FILES_PATH = '/Downloads/vpn'

def SpeedTest():
  """Run speed test and return the results as a tuple.

  Returns:
    tuple of ping, download, and upload speed.
  """
  try:
    output = subprocess.check_output('speedtest --simple', shell=True,
                                     timeout=300)
  except:
    # TODO(scottz): This should raise instead of return a tuple.
    return 'no', 'data', 'returned'

  lines = output.splitlines()
  ping = lines[0].split(b' ')[1].decode('utf-8')
  down = lines[1].split(b' ')[1].decode('utf-8')
  up = lines[2].split(b' ')[1].decode('utf-8')
  return ping, down, up


def VPNConnect(config):
  """Connect to VPN.

  Args:
    The config to connect to.
  Returns:
    None
  """
  # This only works if you built openvpn with password-save enabled.
  cmd = ('sudo openvpn --config %s --ca /home/cowbud/Downloads/vpn/ca.ipvanish.com.crt'
        ' --auth-user-pass auth.txt') % config
  # check_output just to surpress output.
  try:
    subprocess.check_output(cmd, shell=True)
  except:
    pass


def GetExternalIP():
  """Get external IP."""
  url = 'http://icanhazip.com'
  ip = requests.get(url).content.strip()
  return ip.decode('utf-8')


def WaitForIPToChange(initial_ip):
  # TODO this should have a proper timeout.
  # maximum of 25 second wait.
  for i in range(0, 5):
    new_ip = GetExternalIP()
    if new_ip != initial_ip:
      return True

    time.sleep(5)
    continue

  return False


def main():
  initial_ip = GetExternalIP()
#  with open('ip_stats.txt') as stats_fh:
#    processed = [entry.split(',')[0] for entryAin stats_fh]
  processed = []
  for entry in reversed(os.listdir(VPN_FILES_PATH)):
    if not entry.endswith('ovpn'):
      continue
    if 'US' not in entry or entry in processed:
      continue
    time.sleep(3)
    pid = os.fork()
    if pid == 0:
      full_path = os.path.join(VPN_FILES_PATH, entry)
      VPNConnect(full_path)
      return

    if not WaitForIPToChange(initial_ip):
      print('%s,unable, to,connect' % entry)
      os.system('sudo killall -9 openvpn')
      continue
    new_ip = GetExternalIP()
    ping, down, up =  SpeedTest()
    print('%s,%s,%s,%s,%s,%s' % (entry, new_ip, datetime.datetime.now(), ping,
                                 down, up))
    os.system('sudo killall -9 openvpn')
    # do something here to make sure we get our old IP back.


if __name__ == '__main__':
  main()
