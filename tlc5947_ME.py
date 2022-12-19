import machine
import random
import time

class TLC5947:
    def __init__(self, num_channels, sclk_pin, sdin_pin, blank_pin, xlat_pin, pwm_range=4095):
        self.num_channels = num_channels
        self.sclk_pin = sclk_pin
        self.sdin_pin = sdin_pin
        self.blank_pin = blank_pin
        self.xlat_pin = xlat_pin
        self.pwm_range = pwm_range

        # Set up the pins
        self.sclk = machine.Pin(sclk_pin, machine.Pin.OUT)
        self.sdin = machine.Pin(sdin_pin, machine.Pin.OUT)
        self.blank = machine.Pin(blank_pin, machine.Pin.OUT)
        self.xlat = machine.Pin(xlat_pin, machine.Pin.OUT)
        self.xlat.value(0)
        self.blank.value(1)  # Set the BLANK pin high to disable output

        # Initialize the channel data to all zeros
        self.channel_data = [0] * self.num_channels
        self.set_all(0)

    def set_channel(self, channel, value=4095):
        self.channel_data[channel] = value

    def update(self):
        # Set the BLANK pin low to enable output
        self.blank.value(1)

        # Load the channel data
        for value in self.channel_data:
            for i in range(12):
                # rand = random.choice((0,1))
                self.sdin.value((value >> (11 - i)) & 1)
                self.sclk.value(1)
                self.sclk.value(0)

        # Pulse the XLAT pin to latch the data
        self.xlat.value(1)
        self.xlat.value(0)

        # Set the BLANK pin high to disable output
        self.blank.value(0)

    def set_all(self, value: int):
        for reg in self.channel_data:
            reg = value
        self.update()