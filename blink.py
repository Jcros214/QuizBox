# For when you can't tell which Pico you're connected to...

from machine import Pin
from time import sleep

def blink(times: int = 1):
    print(f"Blinking LED {times} times")
    for _ in range(times):
        led = Pin("LED", Pin.OUT)
        led.on()
        sleep(1)
        led.off()


blink()