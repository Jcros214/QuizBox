# from time import time
import utime
from machine import Pin

class DebouncedPin(Pin):
    DEBOUNCE_TIME = 20  # milliseconds

    def __init__(self, pin_id, debounce_time=DEBOUNCE_TIME, *args, **kwargs):
        self.pin_id = pin_id
        super().__init__(pin_id, *args, **kwargs)

        self.debounce_time = debounce_time
        self.timeAtLastUpdate = utime.ticks_ms()
        self.last_value = super().value()

        # Register the event handlers as decorators
        self.on_rise = self.button_pressed_handler(self.on_rise)
        self.on_fall = self.button_pressed_handler(self.on_fall)

        self.irq(trigger=Pin.IRQ_FALLING, handler=self.on_fall)
        self.irq(trigger=Pin.IRQ_RISING, handler=self.on_rise)

    def value(self, *args, **kwargs):
        if utime.ticks_ms() - self.timeAtLastUpdate < self.debounce_time:
            return self.last_value
        else:
            self.last_value = super().value(*args, **kwargs)
            self.timeAtLastUpdate = utime.ticks_ms()
            return self.last_value

    def button_pressed_handler(self, func):
        def debounced_handler(pin):
            current_time = utime.ticks_ms()
            if current_time - self.timeAtLastUpdate >= self.debounce_time:
                func(pin)
            self.timeAtLastUpdate = current_time
        return debounced_handler
