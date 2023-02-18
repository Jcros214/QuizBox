from i2c_display_ME import I2C_Display
from tlc5947_ME import TLC5947

from machine import Pin, time_pulse_us
import time

class DebouncedPin(Pin):
    def __init__(self, pin_id, debounce_time=20, *args, **kwargs):
        self.pin_id = pin_id
        super().__init__(pin_id, *args, **kwargs)
        self.debounce_time = debounce_time
        self.last_bounce_time = 0
        self.last_value = super().value()
        self.irq_handler_rise = None
        self.irq_handler_fall = None

        self.irq(self.on_rise, self.IRQ_RISING)
        self.irq(self.on_fall, self.IRQ_FALLING)
        

    def value(self, *args, **kwargs):
        current_time = time_pulse_us(Pin(self.pin_id), 1)
        if current_time - self.last_bounce_time > self.debounce_time:
            new_value = super().value(*args, **kwargs)
            if new_value != self.last_value:
                self.last_value = new_value
                if new_value == 1 and self.irq_handler_rise is not None:
                    self.irq_handler_rise()
                elif new_value == 0 and self.irq_handler_fall is not None:
                    self.irq_handler_fall()
                self.last_bounce_time = current_time
        return self.last_value

    def irq(self, handler=None, trigger=Pin.IRQ_FALLING):
        if trigger == Pin.IRQ_RISING:
            self.irq_handler_rise = handler
        elif trigger == Pin.IRQ_FALLING:
            self.irq_handler_fall = handler
    
    def on_rise(self):
        pass
    
    def on_fall(self):
        pass



class QuizBox:
    boxState = 1
    
    class Quizzer:
        color = 0xF66733
        def __init__(self, seat: int = -1, switch: int = -1, num: int = -1) -> None:
            self.seatpin = Pin(seat, pull=Pin.PULL_UP)
            self.switchpin = Pin(switch, pull=Pin.PULL_UP)
            self.num = num

            self.seatval = self.seatpin.value()
            self.switchval = self.switchpin.value()
        
        @property
        def seatread(self):
            self.seatval = not self.seatpin.value()
            return self.seatval

        @property
        def switchread(self):
            self.switchval = not self.switchpin.value()
            return self.switchval

        @property
        def bothread(self):
            return (self.switchread, self.seatread)
    class Buzzer(Pin):
        def __init__(self, id = 16):
            super().__init__(id, Pin.PULL_UP)

        def buzz(self, time: int):
            ...

    class Reset(DebouncedPin):
        def __init__(self, id = 17):
            super().__init__(id, Pin.PULL_UP)

        def on_rise(self, pin):
            pass

        def on_fall(self, pin):
            print("reset fell")
            QuizBox.boxState = QuizBox.boxState + 1 if QuizBox.boxState < 3 else 0


    def __init__(self) -> None:
        self.display = I2C_Display()
        self.tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

        self.reset = self.Reset()
        self.buzzer = self.Buzzer()

        self.quizzers = [
            self.Quizzer(10, 18, 1),
            self.Quizzer(11, 19, 2),
            self.Quizzer(12, 20, 3),
            self.Quizzer(13, 21, 4),
            self.Quizzer(14, 22, 5),
        ]

        self.cycle_ctr = 0

    def update(self):
        self.cycle_ctr += 1
        if self.cycle_ctr % 1000 == 0:
            print("Cycle {}".format(self.cycle_ctr))
        if self.boxState == 1:
            for quizzer in self.quizzers:
                if quizzer.bothread == (True,True):
                    self.tlc.set_led(quizzer.num - 1, 1)
                else:
                    self.tlc.set_led(quizzer.num - 1, 0)
            self.tlc.update()

        elif self.boxState == 2:
            for quizzer in self.quizzers:
                if quizzer.bothread == (True,True):
                    self.tlc.set_led(quizzer.num - 1, 1)
                    self.tlc.update()
                    self.boxState = 3
                    break

        elif self.boxState == 3:
            ...
        else:
            self.boxState = 1
            raise ValueError("BoxState should be in [1,2,3]. Setting to 1")

if __name__ == '__main__':
    box = QuizBox()
    # tlc = TLC5947(24, sclk_pin=2, sdin_pin=3, blank_pin=4, xlat_pin=5)

    while True:
        box.update()
        # time.sleep(1)
