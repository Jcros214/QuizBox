from machine import Pin 
from debounced_pin import DebouncedPin

# import logging

from i2c_display_ME import I2C_Display
from tlc5947_ME import TLC5947
from quizzer import Quizzer
from color import Color


from time import sleep
import utime

# class DebouncedPin(Pin):
#     def __init__(self, pin_id, debounce_time=20, *args, **kwargs):
#         self.pin_id = pin_id
#         super().__init__(pin_id, *args, **kwargs)
#         self.debounce_time = debounce_time
#         self.last_bounce_time = 0
#         self.last_value = super().value()
#         self.irq_handler_rise = None
#         self.irq_handler_fall = None

#         self.irq(self.on_rise, self.IRQ_RISING)
#         self.irq(self.on_fall, self.IRQ_FALLING)
        

#     def value(self, *args, **kwargs):
#         current_time = time_pulse_us(Pin(self.pin_id), 1)
#         if current_time - self.last_bounce_time > self.debounce_time:
#             new_value = super().value(*args, **kwargs)
#             if new_value != self.last_value:
#                 self.last_value = new_value
#                 if new_value == 1 and self.irq_handler_rise is not None:
#                     self.irq_handler_rise()
#                 elif new_value == 0 and self.irq_handler_fall is not None:
#                     self.irq_handler_fall()
#                 self.last_bounce_time = current_time
#         return self.last_value

#     def irq(self, handler=None, trigger=Pin.IRQ_FALLING):
#         if trigger == Pin.IRQ_RISING:
#             self.irq_handler_rise = handler
#         elif trigger == Pin.IRQ_FALLING:
#             self.irq_handler_fall = handler
    
#     def on_rise(self):
#         pass
    
#     def on_fall(self):
#         pass



class QuizBox:
    DEBUG_MODE = True
    boxState = 1
    boxStateHasChanged = False
    displaytimer = 0
    displaytimerbuffer = 0
    color = Color.fromHex("#F56600")

    # Colors at state [front, back]
    # colors = {
    #     1: [amber, green],
    #     2: [off, amber],
    #     3: [red, red]
    # }

    # Colors at state [front, back]
    colors = {
        1: [Color.fromHex("#FFBF00"), Color.fromHex("#00FF00")],
        2: [Color.fromHex("#000000"), Color.fromHex("#FFBF00")],
        3: [Color.fromHex("#FF0000"), Color.fromHex("#FF0000")]
    }



    class Timer:
        def __init__(self):
            self.start = utime.time()
            self.seconds = 0
            self.lastWholeSecond = 0

        def startCoutndown(self, time: int):
            self.start = utime.time()
            self.seconds = time

        

        def wholeSecondsRemaining(self):
            self.lastWholeSecond = round(self.seconds - (utime.time() - self.start))
            return self.lastWholeSecond
            
        def wholeSecondHasChanged(self):
            if self.lastWholeSecond != self.wholeSecondsRemaining():
                return True
            return False



    class Buzzer(Pin):
        def __init__(self, id = 16):
            super().__init__(id, Pin.PULL_UP)

        def buzz(self, time: float):
            if not QuizBox.DEBUG_MODE:
                self.high()
                sleep(time)
                self.low()
            else:
                print("Skipping buzzing due to debug mode")

    class Reset(DebouncedPin):
        def __init__(self, id=28):
            super().__init__(id, 200, DebouncedPin.IN, DebouncedPin.PULL_UP)

            print("initing reset")

        def on_rise(self, pin):
            print("reset rose")
            # if the value acutally rose
            if self.value() == 1:
                QuizBox.resetUpdate()


        def on_fall(self, pin):
            print("reset fell")





    def __init__(self) -> None:

        print("Initializing QuizBox\n---------------_")
        print("Debug mode: " + "Enabled" if QuizBox.DEBUG_MODE else "Disabled")

        self.tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

        self.display = I2C_Display()

        self.reset = self.Reset()

        self.timer = self.Timer()

        # self.reset = Pin(28, Pin.IN, Pin.PULL_UP)

        self.buzzer = self.Buzzer()

        self.quizzers = [
            Quizzer(10, 18, 1),
            Quizzer(11, 19, 2),
            Quizzer(12, 20, 3),
            Quizzer(13, 21, 4),
            Quizzer(14, 22, 5),
        ]

        self.cycle_ctr = 0
        self.boxStateChange()

        if QuizBox.DEBUG_MODE:
            print("Debug mode enabled")
            print("Finished initializing QuizBox\n----------------")

    

    def update(self):
        # Set state lights to box state
        for led, color in zip([5,6], self.colors[QuizBox.boxState]):
            self.tlc.set_led_rgb(led, color)

        # self.cycle_ctr += 1
        # if self.cycle_ctr % 1000 == 0:
            # print(f"Cycle {self.cycle_ctr}\nBoxState: {QuizBox.boxState}\nReset: {self.reset.value()}\nTimer: {self.timer.wholeSecondsRemaining()}\n")
        
        if QuizBox.boxStateHasChanged:
            self.boxStateChange()
            QuizBox.boxStateHasChanged = False
        
        if QuizBox.boxState == 1:

            for quizzer in self.quizzers:
                if quizzer.bothread == (True,True):
                    self.tlc.set_led_rgb(quizzer.num - 1, QuizBox.color)
                else:
                    self.tlc.set_led(quizzer.num - 1, 0)
            self.tlc.update()

        elif QuizBox.boxState == 2:

            for quizzer in self.quizzers:
                if quizzer.bothread == (True,True):
                    self.tlc.set_led_rgb(quizzer.num - 1, QuizBox.color)
                    self.tlc.update()
                    self.buzzer.buzz(0.5)
                    QuizBox.setBoxState(3)
                    break

        elif QuizBox.boxState == 3:
            # Set display to show who jumped, show countdown 
            if self.timer.lastWholeSecond >= 0:
                if self.timer.wholeSecondHasChanged():
                    self.display.move_to(0,1)
                    if self.timer.lastWholeSecond > 9:
                        self.display.putstr(f"{self.timer.wholeSecondsRemaining()}")
                    else:
                        self.display.putstr(f" {self.timer.wholeSecondsRemaining()}")
            else:
                self.setBoxState(1)



        else:
            QuizBox.setBoxState(1)
            raise ValueError("ERROR: BoxState should be in [1,2,3]. Setting to 1")
    
    @staticmethod
    def resetUpdate():
        if QuizBox.boxState==1:
            QuizBox.setBoxState(2)
        elif QuizBox.boxState==2:
            QuizBox.setBoxState(1)
        elif QuizBox.boxState==3:
            QuizBox.setBoxState(1)

        else:
            raise ValueError("ERROR: BoxState should be in [1,2,3]. Setting to 1")


    @staticmethod
    def setBoxState(state):
        print(f"Setting boxState from {QuizBox.boxState} to {state} ({round(utime.time(),2)})")
        QuizBox.boxState = state
        QuizBox.boxStateHasChanged = True

    def boxStateChange(self):
        self.display.clear()

        stateDict = {
            1: "Standby",
            2: "Armed",
            3: "Locked"
        }

        self.display.putstr(f"State: {stateDict[QuizBox.boxState]}")

        if QuizBox.boxState == 3:
            self.timer.startCoutndown(32)

    # TODO: Implement this
    def sendToConnectedBoxes(self):
        pass


if __name__ == '__main__':
    box = QuizBox()
    # tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

    while True:
        box.update()
        # time.sleep(1)
