from machine import Pin
import machine

class TLC5947:
    def __init__(self, clock: int = 2, data: int = 3, latch: int = 5):
        self.numdrivers = 1
        self.data = Pin(data, Pin.OUT)
        self.clock = Pin(clock, Pin.OUT)
        self.latch = Pin(latch, Pin.OUT)

        self.latch.low()

        self._spi = machine.SPI(0)

        # self.OE = OE

        self.pwmbuffer = [0] * (24 * 2 * self.numdrivers)         # memset(pwmbuffer, 0, 2 * 24 * n);
        # self.spi = machine.SPI(0)

    def write(self):
        self.latch.low()                                        #        digitalWrite(_lat, LOW);
                                                                #            // 24 channels per TLC5974
        for c in range(24 * self.numdrivers - 1, -1, -1):       #            for (int16_t c = 24 * numdrivers - 1; c >= 0; c--) {
                                                                #                // 12 bits per channel, send MSB first
            for b in range(11, -1, -1):                         #                for (int8_t b = 11; b >= 0; b--) {
                self.clock.low()                                #                    digitalWrite(_clk, LOW);
                if self.pwmbuffer[c] & (1 << b):                #                    if (pwmbuffer[c] & (1 << b))
                    self.data.high()                            #                        digitalWrite(_dat, HIGH);
                else:                                           #                    else
                    self.data.low()                             #                        digitalWrite(_dat, LOW);
                                                                #
                self.clock.high()                               #                    digitalWrite(_clk, HIGH);
                                                                #                }
                                                                #            }
        self.clock.low()                                        #        digitalWrite(_clk, LOW);
        self.latch.high()                                       #        digitalWrite(_lat, HIGH);
        self.latch.low()                                        #        digitalWrite(_lat, LOW);

    def setLed(self, lednum, r,g,b):
        self.setPWM(lednum * 3, r)
        self.setPWM(lednum * 3 + 1, g)
        self.setPWM(lednum * 3 + 2, b)

    def setPWM(self, chan: int, pwm: int):
        if (pwm > 4095):
            pwm = 4095
        try:
            self.pwmbuffer[chan] = pwm
        except:
            pass

