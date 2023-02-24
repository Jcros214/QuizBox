class Color:
    def __init__(self):
        self.twelvebitr = 0
        self.twelvebitg = 0
        self.twelvebitb = 0

    def fromHex(self, hex: str):
        self.twelvebitr = int(hex[1:3], 16) * 16
        self.twelvebitg = int(hex[3:5], 16) * 16
        self.twelvebitb = int(hex[5:7], 16) * 16
        return self

    def fromRGB(self, r: int, g: int, b: int):
        self.twelvebitr = r * 16
        self.twelvebitg = g * 16
        self.twelvebitb = b * 16
        return self