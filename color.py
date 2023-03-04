class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = r
        self.g = g
        self.b = b

    def getValueAs8Bit(self) -> tuple[int, int, int]:
        return int(self.r*256), int(self.g*256), int(self.b*256)

    def getValueAs12Bit(self) -> tuple[int, int, int]:
        return int(self.r*4096), int(self.g*4096), int(self.b*4096)

    @staticmethod
    def fromHex(hex: str):
        color = Color()
        color.r = int(hex[1:3], 16) / 255
        color.g = int(hex[3:5], 16) / 255
        color.b = int(hex[5:7], 16) / 255
        return color

    @staticmethod
    def fromRGB(r: int, g: int, b: int):
        color = Color()
        color.r = r // 255
        color.g = g // 255
        color.b = b // 255
        return color

    @staticmethod
    def lerp(color1: 'Color', color2: 'Color', t: float) -> 'Color':
        r = (1 - t) * color1.r + t * color2.r
        g = (1 - t) * color1.g + t * color2.g
        b = (1 - t) * color1.b + t * color2.b
        color = Color()
        color.r = int(r)
        color.g = int(g)
        color.b = int(b)
        return color


    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b})"

