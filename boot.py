BRANCH = 'sandbox'

# Startup script
# Connect to the internet, download main.py from github, and run it
# If unable to connect, use last saved main.py

import rp2
import network
import ubinascii
import machine
import urequests as requests
import time
from secrets import secrets
import socket

# Set country to avoid possible errors
rp2.country('US')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode
# wlan.config(pm = 0xa11140)

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('mac = ' + mac)

# Other things to query
# print(wlan.config('channel'))
# print(wlan.config('essid'))
# print(wlan.config('txpower'))

# Load login data from different file for safety reasons
ssid = secrets['ssid']
pw = secrets['pw']

wlan.connect(ssid, pw)

# Wait for connection with 10 second timeout
timeout = 10
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    timeout -= 1
    print('Waiting for connection...')
    time.sleep(1)


# Define blinking function for onboard LED to indicate error codes
def blink_onboard_led(num_blinks):
    led = machine.Pin('LED', machine.Pin.OUT)
    for i in range(num_blinks):
        led.on()
        time.sleep(.2)
        led.off()
        time.sleep(.2)


# Handle connection error
# Error meanings
# 0  Link Down
# 1  Link Join
# 2  Link NoIp
# 3  Link Up
# -1 Link Fail
# -2 Link NoNet
# -3 Link BadAuth

wlan_status = wlan.status()
blink_onboard_led(wlan_status)

if wlan_status != 3:
    raise RuntimeError('Wi-Fi connection failed')
else:
    print('Connected')
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# door_bell = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN)

# last_state = False
# current_state = False

github_api_url = f"https://api.github.com/repos/jcros214/QuizBox/branches/{BRANCH}"

api_request = requests.get(github_api_url, headers={'User-Agent': 'jcros214'})

if api_request.status_code == 200:
    checksum = api_request.json()['commit']['sha']
    print(checksum)
    with open('main_py_checksum.txt', 'w') as f:
        f.write(checksum)

    main_py_update_url = f"https://raw.githubusercontent.com/Jcros214/QuizBox/{BRANCH}/main.py"

    request = requests.get(main_py_update_url)
    code = str(request.content, 'utf-8')

    if code.find('main()') != -1:
        print('main() found')
        # Save main.py to flash
        with open('main.py', 'w') as f:
            f.write(code)
