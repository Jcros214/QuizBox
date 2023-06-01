from machine import Pin 
from debounced_pin import DebouncedPin

# import logging

from i2c_display_ME import I2C_Display
from tlc5947_ME import TLC5947
from quizzer import Quizzer
from color import Color
from Box2Box import Box2Box


from time import sleep
import utime


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
        1: [Color.fromHex("#806000"), Color.fromHex("#008000")],
        2: [Color.fromHex("#000000"), Color.fromHex("#806000")],
        3: [Color.fromHex("#800000"), Color.fromHex("#800000")]
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
        def __init__(self, id = 14):
            super().__init__(id, Pin.PULL_UP)

        def buzz(self, time: float):
            if not QuizBox.DEBUG_MODE:
                self.high()
                sleep(time)
                self.low()
            else:
                print("Skipping buzzing due to debug mode")

    class Reset(DebouncedPin):
        def __init__(self, id=15):
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

        print("Initializing QuizBox\n----------------")
        print("Debug mode: " + "Enabled" if QuizBox.DEBUG_MODE else "Disabled")

        self.tlc = TLC5947()

        self.display = I2C_Display()
        self.display.putstr("   QuizBox 1.0.0    \n")

        self.reset = self.Reset()

        self.timer = self.Timer()

        self.buzzer = self.Buzzer()

        self.coms = Box2Box()

        self.coms.setState1(lambda holding: (QuizBox.setBoxState(1), self.overide_holding(holding)))
        self.coms.setState2(lambda: QuizBox.setBoxState(2))
        self.coms.setState3(lambda x: QuizBox.setBoxState(3))



        self.quizzers = [
            Quizzer(16, 21, 1),
            Quizzer(17, 22, 2),
            Quizzer(18, 26, 3),
            Quizzer(19, 27, 4),
            Quizzer(20, 28, 5),
        ]

        self.cycle_ctr = 0
        self.boxStateChange()

        if QuizBox.DEBUG_MODE:
            print("Debug mode enabled")
            print("Finished initializing QuizBox\n----------------")

    def update(self):
        # print("Still alive...")

        if (msg := self.coms.update()) != None and len(msg) > 0:
            self.display.clear()
            self.display.putstr(msg)
            print(msg)
        
        # print([(self.quizzers[i].switchpin, self.quizzers[i].switchval) for i  in range(5)])

        # Set state lights to box state
        for led, color in zip([5,6], self.colors[QuizBox.boxState]):
            self.tlc.set_led_rgb(led, color)
        self.tlc.update()


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
                # self.setBoxState(1)
                ...

        else:
            QuizBox.setBoxState(1)
            raise ValueError("ERROR: BoxState should be in [1,2,3]. Setting to 1")
        
    def override_holding(self, holding: bool | None = None):
        if holding != None:
            self.HOLDING_OVERRIDE = holding


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

        if state in [1,2,3]:
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

        # Messages should be instructions.
        b"<S: 1>"
        b"<S: 1, Holding>"
        b"<S: 2>"
        b"<S: 3, Timer: {}>"

        param = ''

        if QuizBox.boxState == 1:
            param = ', Holding' if not self.reset.value() else ''
        elif QuizBox.boxState == 3:
            param = f", Timer: {self.timer.wholeSecondsRemaining()}"

        self.coms.write(f"<S: {QuizBox.boxState}{param}>")
        print(f'sent state f"<S: {QuizBox.boxState}{param}>"')

        if QuizBox.boxState == 3:
            self.timer.startCoutndown(32)

    # TODO: Implement this
    def sendToConnectedBoxes(self):
        pass

def main():
    box = QuizBox()

    while True:
        box.update()

if __name__ == '__main__':
    main()