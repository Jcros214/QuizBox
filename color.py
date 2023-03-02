class Color:
    def __init__(self):
        self.twelvebitr = 0
        self.twelvebitg = 0
        self.twelvebitb = 0

    @staticmethod
    def fromHex(hex: str):
        color = Color()

        color.twelvebitr = int(hex[1:3], 16) * 16
        color.twelvebitg = int(hex[3:5], 16) * 16
        color.twelvebitb = int(hex[5:7], 16) * 16
        return color

    @staticmethod
    def fromRGB(r: int, g: int, b: int):
        color = Color()
        color.twelvebitr = r * 16
        color.twelvebitg = g * 16
        color.twelvebitb = b * 16
        return color

    @staticmethod
    def lerp(color1: 'Color', color2: 'Color', t: float) -> 'Color':
        r = (1 - t) * color1.twelvebitr + t * color2.twelvebitr
        g = (1 - t) * color1.twelvebitg + t * color2.twelvebitg
        b = (1 - t) * color1.twelvebitb + t * color2.twelvebitb
        color = Color()
        color.twelvebitr = int(r)
        color.twelvebitg = int(g)
        color.twelvebitb = int(b)
        return color

    
    def __repr__(self) -> str:
        return f"Color({self.twelvebitr}, {self.twelvebitg}, {self.twelvebitb})"