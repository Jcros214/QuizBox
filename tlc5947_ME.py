import machine
import random
import time

# def convert_8bit_to_12bit(color):
#     r,g,b = color
#     r = (r << 4) | (r >> 4)
#     g = (g << 4) | (g >> 4)
#     b = (b << 4) | (b >> 4)
#     return (r, g, b)


# def hex_to_rgb(hex_value):
#     hex_string = hex(hex_value).lstrip('0x')
#     if len(hex_string) < 6:
#         hex_string = '0' * (6 - len(hex_string)) + hex_string
#     output = tuple(int(hex_string[i:i+2], 16) for i in (0, 2, 4))

#     return convert_8bit_to_12bit(output)

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

    def update(self):
        # Check the state changed flag
        if not self.state_changed:
            return

        # Set the BLANK pin low to enable output
        self.blank.value(1)

        # Load the channel data
        for value in self.channel_data:
            for i in range(0, 12):
                self.sdin.value((value >> i) & 1)
                self.sclk.value(1)
                self.sclk.value(0)

        # Pulse the XLAT pin to latch the data
        self.xlat.value(1)
        self.xlat.value(0)
        # Set the BLANK pin high to disable output
        # self.blank.value(0)

        # Reset the state changed flag
        self.state_changed = False

    def set_channel(self, channel, value=4095//2):
        gamma = 2.5
        value = int(pow(value / 255.0, gamma) * 255.0 + 0.5)
        # Only set the channel data and the state changed flag if the value is different
        if value != self.channel_data[-channel-1]:
            self.channel_data[-channel-1] = value
            self.state_changed = True
    # # Set LED to hex value
    # def set_led(self, led, value: int):
    #     # Convert the hexadecimal color value to a tuple of 8-bit RGB values
    #     rgb_8bit = hex_to_rgb(value)
    #     # Convert the 8-bit RGB values to 12-bit values
    #     # rgb_12bit = convert_8bit_to_12bit(rgb_8bit)
    #     # Set the values for the red, green, and blue channels of the LED
    #     self.set_channel(led*3, rgb_8bit[0])
    #     self.set_channel(led*3+1, rgb_8bit[1])
    #     self.set_channel(led*3+2, rgb_8bit[2])
    def set_led(self, id, inten = .5):
        self.set_channel(id*3  , int(4095*inten))
        self.set_channel(id*3+1, int(4095*inten))
        self.set_channel(id*3+2, int(4095*inten))
        




    def set_all(self, value: int):
        for reg in self.channel_data:
            reg = value
        self.update()