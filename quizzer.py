from machine import Pin

class Quizzer:
    color = 0xF66733
    def __init__(self, seat: int = -1, switch: int = -1, num: int = -1) -> None:
        self.seatpin = Pin(seat, pull=Pin.PULL_UP)
        self.switchpin = Pin(switch, pull=Pin.PULL_UP)
        self.num = num

        self.seatval = self.seatpin.value()
        self.switchval = self.switchpin.value()
    
    @property
    def getSeat(self):
        self.seatval = not self.seatpin.value()
        return self.seatval

    @property
    def getSwitch(self):
        self.switchval = not self.switchpin.value()
        return self.switchval

    @property
    def bothread(self):
        return (self.getSwitch, self.getSeat)
