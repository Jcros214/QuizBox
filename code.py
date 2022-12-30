from QuizBoxIO import QuizBox
# from tlc5947_ME import TLC5947
import time

box = QuizBox()
# tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

while True:
    box.update()
    time.sleep(1)
