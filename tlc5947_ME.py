import machine
from color import Color
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
    def __init__(self, num_channels=24, sclk_pin=9, sdin_pin=8, blank_pin=10, xlat_pin=11, pwm_range=4095):
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
        self.blank.value(1)  # Set the BLANK pin high to disable output
        self.xlat = machine.Pin(xlat_pin, machine.Pin.OUT)
        self.xlat.value(0)

        # Set the state changed flag
        self.state_changed = False

        self.blank.value(0)

        # Initialize the channel data to all zeros
        self.channel_data = [0] * self.num_channels
        self.set_all(0)
        self.set_channel(23, 100)
        self.update()

        # for i in range(0, 4095,10):
        #     self.set_all(i)
        #     self.update()
        #     time.sleep(0.001)

    def update(self):
        # Check the state changed flag
        if not self.state_changed:
            return

        # Set the BLANK pin low to enable output
        # self.blank.value(1)


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

    def set_led(self, id, inten = .5):
        self.set_channel(id*3  , int(4095*inten))
        self.set_channel(id*3+1, int(4095*inten))
        self.set_channel(id*3+2, int(4095*inten))
        

    def set_led_rgb(self, led: int, color: Color):

        channels = [led for led in range(led*3, led*3+3)]

        # Set the values for the red, green, and blue channels of the LED
        for ch, cl in zip(channels, color.getValueAs12Bit()):
            self.set_channel(ch, cl)


    def set_all(self, value: int):
        for ch in range(24):
            self.set_channel(ch, value)
        self.update()

    def set_all_rgb(self, color: Color):
        for led in range(8):
            self.set_led_rgb(led, color)
        self.update()


    # def fade_between_colors(self, start_color: Color, end_color: Color, msec: float):
    #     start_time = time.ticks_ms()
    #     end_time = start_time + (msec)

    #     while time.ticks_ms() < end_time:
    #         self.set_all_rgb(Color.lerp(start_color, end_color, time.ticks_ms() / end_time))

    #     self.set_all_rgb(end_color)



        # # Precompute the array of colors
        # colors = []
        # for i in range(self.num_channels // 3):
        #     r,g,b = int(start_color.twelvebitr + (end_color.twelvebitr - start_color.twelvebitr) * i / (self.num_channels // 3 - 1)), int(start_color.twelvebitg + (end_color.twelvebitg - start_color.twelvebitg) * i / (self.num_channels // 3 - 1)), int(start_color.twelvebitb + (end_color.twelvebitb - start_color.twelvebitb) * i / (self.num_channels // 3 - 1))

        #     print(r,g,b)
        #     input(0)

        #     color = Color.fromRGB(r,g,b)
        #     colors.append(color)

        # print(colors)

        # # Loop over the array of colors
        # for color in colors:
        #     elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)

        #     # Set all LEDs to the current color
        #     for led in range(self.num_channels // 3):
        #         self.set_led_rgb(led, color)
        #     self.update()

        #     # Sleep for the remaining time
        #     remaining_time = duration - elapsed_time
        #     # if remaining_time > 0:
        #     #     time.sleep_ms(int(remaining_time))

        # self.set_all(0)





from time import sleep

def tlc_loop():
    tlc = TLC5947()

    while True:
        for ch in range(24):
            tlc.set_channel(ch, 4095//2)
            tlc.update()
            sleep(0.3)
            tlc.set_channel(ch, 0)

if __name__ == "__main__":
    tlc_loop()