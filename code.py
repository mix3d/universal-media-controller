import board
import digitalio
import usb_hid
import time
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

dirPin = digitalio.DigitalInOut(board.GP20)
stepPin = digitalio.DigitalInOut(board.GP19)
dirPin.direction = digitalio.Direction.INPUT
stepPin.direction = digitalio.Direction.INPUT

dirPin.pull = digitalio.Pull.UP
stepPin.pull = digitalio.Pull.UP

UP = 1
DOWN = -1
FORWARD = UP
BACKWARD = DOWN
MEDIA = 1
KEY = 2
DEBOUNCE = 80 # time in ms

pins = [
  board.GP10,
  board.GP11,
  board.GP12,
  board.GP13,
  board.GP14
]

keyMap = {
  0: (MEDIA, ConsumerControlCode.SCAN_PREVIOUS_TRACK),
  1: (MEDIA, ConsumerControlCode.SCAN_NEXT_TRACK),
  2: (MEDIA, ConsumerControlCode.PLAY_PAUSE),
  3: (MEDIA, ConsumerControlCode.MUTE),
  # 3: (KEY, ConsumerControlCode.SCAN_NEXT_TRACK),
  # 4: (MEDIA, ConsumerControlCode.SCAN_NEXT_TRACK),
}

class Switch:
  def __init__(self, pin):
    self.pin = pin
    self.lastTime = -1
    self.lastValue = False

switches = [] # type: List[Switch]
for gp in pins:
  pin = digitalio.DigitalInOut(gp)
  pin.direction = digitalio.Direction.INPUT
  pin.pull = digitalio.Pull.UP
  switches.append(Switch(pin))

prevNextCode = 0

def volume(dir):
  cc.send(ConsumerControlCode.VOLUME_DECREMENT if dir == DOWN else ConsumerControlCode.VOLUME_INCREMENT)

def skip(dir):
  cc.send(ConsumerControlCode.SCAN_NEXT_TRACK if dir == FORWARD else ConsumerControlCode.SCAN_PREVIOUS_TRACK)

def mute():
  cc.send(ConsumerControlCode.MUTE)

def pressKey(index):
  key = keyMap[index]
  if key[0] == MEDIA:
    cc.send(key[1])
  if key[0] == KEY:
    kbd.press(key[1])

def releaseKey(index):
  key = keyMap[index]
  if key[0] == KEY:
    kbd.release(key[1])

def checkAndToggleSwitch(index):
  global switches # type: List[Switch]
  switch = switches[i]
  if time.ticks_ms() - switch.lastTime > DEBOUNCE:
    if switch.lastValue != switch.pin.value:
      switch.lastValue = switch.pin.value
      try:
        if switch.lastValue: pressKey(index)
        else: releaseKey(index)
      except ValueError:
        pass

previousValue = False
def readEncoder():
    global previousValue
    global stepPin
    global dirPin

    if previousValue != stepPin.value:
      if stepPin.value == False:
        if dirPin.value == True:
          volume(DOWN)
        else:
          volume(UP)
      else:
        if dirPin.value == False:
          volume(DOWN)
        else:
          volume(UP)
      previousValue = stepPin.value

# original encoder reading was erratic and noisy
# enhanced logic from www.best-microcontroller-projects.com/rotary-encoder.html
store = 0
def readEncoderFancy():
  global prevNextCode
  global store
  # Table of valid vs invalid combinations based on encoder reading combinations
  rot_enc_table = [0,1,1,0,1,0,0,1,1,0,0,1,0,1,1,0]
  prevNextCode <<= 2
  if stepPin.value: prevNextCode |= 0x02
  if dirPin.value: prevNextCode |= 0x01
  prevNextCode &= 0x0f

  if rot_enc_table[prevNextCode] == 1:
    store <<= 4
    store |= prevNextCode
    if store & 0x2b: return True #-1
    if store & 0xff: return True # 1
  return False #0

def handleEncoder():
  global prevNextCode
  if readEncoderFancy():
    # Added additional state values that were consistent and valid with 2nd detent values
    # Possibly only an issue with the RKJXTF42001's encoder?
    if prevNextCode == 0x0b or prevNextCode == 13:
      volume(DOWN) # Left
      print("LEFT :"+str(prevNextCode))
    if prevNextCode == 0x07 or prevNextCode == 8:
      volume(UP) # Right
      print("RIGHT :"+str(prevNextCode))

while 1==1:
  handleEncoder()

