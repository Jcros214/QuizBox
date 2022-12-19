# My modules
from i2c_display_ME import I2C_Display
from tlc5947_ME import TLC5947

# External modules
import time

display = I2C_Display()
tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

while True:
    for channel in range(24):
        # print(channel)
        tlc.set_channel(channel, 4095//4)
        tlc.update()
        time.sleep(.1)
        tlc.set_channel(channel, 0)
        tlc.update()
        time.sleep(.1)