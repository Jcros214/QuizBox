BRANCH = 'sandbox'

# ----------------------------------------------------------------------------------------------------
# Package Imports
# ----------------------------------------------------------------------------------------------------
from time import sleep
import utime
from machine import Pin, UART, I2C
import time
import utime
import gc
from time import sleep
import re


# ----------------------------------------------------------------------------------------------------
# Custom Exceptions
# ----------------------------------------------------------------------------------------------------
class HardwareError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


# ----------------------------------------------------------------------------------------------------
# Color
# ----------------------------------------------------------------------------------------------------
class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = r
        self.g = g
        self.b = b

    def getValueAs8Bit(self) -> tuple[int, int, int]:
        return int(self.r * 256), int(self.g * 256), int(self.b * 256)

    def getValueAs12Bit(self) -> tuple[int, int, int]:
        return int(self.r * 4096), int(self.g * 4096), int(self.b * 4096)

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


# ----------------------------------------------------------------------------------------------------
# Debounced Pin
# ----------------------------------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------------------------------
# Quizzer
# ----------------------------------------------------------------------------------------------------
class Quizzer:
    color = 0xF66733

    def __init__(self, seat: int = -1, switch: int = -1, num: int = -1) -> None:
        self.seatpin = Pin(seat, mode=Pin.IN, pull=Pin.PULL_UP)
        self.switchpin = Pin(switch, mode=Pin.IN, pull=Pin.PULL_UP)
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


# ----------------------------------------------------------------------------------------------------
# QuizSite
# ----------------------------------------------------------------------------------------------------
class QuizSite:
    def __init__(self) -> None:
        pass
        # Establish connection to internet

    def get(self, key) -> str:
        # Get value from internet
        return str()

    def post() -> None:
        # Post value to internet
        pass


# ----------------------------------------------------------------------------------------------------
# Box2Box
# ----------------------------------------------------------------------------------------------------
class Box2Box:
    """
    Messages should be instructions.
    
    b"<S: 1>"
    b"<S: 1, Holding>"
    b"<S: 2>"
    b"<S: 3, Timer: {}>"

    """
    LATEST_MSG = None

    class Message:
        def __init__(self, msg: bytes | None, sender: UART) -> None:
            if msg is None:
                self.msg = b""
            else:
                self.msg = msg

            self.sender = sender

        @staticmethod
        def init_from_str(msg: str, sender: UART):
            return Box2Box.Message(msg.encode("utf-8"), sender)

        def getMsg(self):
            if self.msg is None:
                return None

            message = str(self)
            latest_msg = ""

            for ind in range(len(message)):
                if message[-(ind + 1)] == "<":
                    latest_msg = message[-ind:-1]
                    break
            else:
                return None

            if latest_msg == "S: 1" or latest_msg == "S: 1, Holding" or latest_msg == "S: 2" or latest_msg.startswith(
                    "S: 3, Timer: "):
                return latest_msg
            else:
                return None
                # raise error?

        def __str__(self) -> str:
            try:
                return self.msg.decode("utf-8")
            except:
                return ''

        def __bytes__(self) -> bytes:
            return self.msg

    # TX,RX,INT,ACK
    COM1 = [0, 1, 2, 3]
    COM2 = [4, 5, 6, 7]

    def __init__(self) -> None:
        self.com_left = UART(0, 9600, tx=Pin(Box2Box.COM1[0]), rx=Pin(Box2Box.COM1[1]))
        self.com_right = UART(1, 9600, tx=Pin(Box2Box.COM2[0]), rx=Pin(Box2Box.COM2[1]))

        # lambda functions:
        self._state1 = lambda holding: None
        self._state2 = lambda: None
        self._state3 = lambda x: None

    def update(self) -> str | None:
        msg = self.getInput()
        if msg:
            return self.parseInput(msg)

    def getInput(self):
        messages = [self.Message(self.com_left.read(), self.com_left),
                    self.Message(self.com_right.read(), self.com_right)]

        for msg in messages:
            if msg.msg:
                return msg

    def parseInput(self, message: Message) -> None | str:
        msg = message.getMsg()

        if msg is None:
            return

        # if Box2Box.LATEST_MSG != message:
        #     Box2Box.LATEST_MSG = message
        #     self.write(msg, self.getOtherCom(message.sender))

        if msg[3] == '1':
            if msg[6:13] == "Holding":
                try:
                    self._state1(holding=True)
                except Exception as e:
                    print(f'tried to call state1 holding but {e}')
                return msg
            else:
                try:
                    self._state1(holding=False)
                except Exception as e:
                    print(f'tried to call state1 but {e}')
                return msg
        elif msg[3] == '2':
            try:
                self._state2()
            except Exception as e:
                print(f'tried to call state2 but {e}')
            return msg
        elif msg[3] == '3':
            try:
                self._state3(int(msg[13:]))
            except Exception as e:
                print(f'tried to call state3 but {e}')
            return msg
        else:
            print(f'Malformed input: "{msg}"')

    def getOtherCom(self, com: UART) -> UART:
        if com == self.com_left:
            return self.com_right
        else:
            return self.com_left

    def setState1(self, state):
        self._state1 = state

    def setState2(self, state):
        self._state2 = state

    # Note that state3 is a lambda function that takes in an int.
    def setState3(self, state):
        self._state3 = state

    def write(self, msg: str, com: UART | None = None):
        if com:
            com.write(msg.encode("utf-8"))
        else:
            for com in [self.com_left, self.com_right]:
                com.write(msg.encode("utf-8"))


# ----------------------------------------------------------------------------------------------------
# I2C Display
# ----------------------------------------------------------------------------------------------------
class LcdApi:
    # Implements the API for talking with HD44780 compatible character LCDs.
    # This class only knows what commands to send to the LCD, and not how to get
    # them to the LCD.
    #
    # It is expected that a derived class will implement the hal_xxx functions.
    #
    # The following constant names were lifted from the avrlib lcd.h header file,
    # with bit numbers changed to bit masks.

    # HD44780 LCD controller command set
    LCD_CLR = 0x01  # DB0: clear display
    LCD_HOME = 0x02  # DB1: return to home position

    LCD_ENTRY_MODE = 0x04  # DB2: set entry mode
    LCD_ENTRY_INC = 0x02  # DB1: increment
    LCD_ENTRY_SHIFT = 0x01  # DB0: shift

    LCD_ON_CTRL = 0x08  # DB3: turn lcd/cursor on
    LCD_ON_DISPLAY = 0x04  # DB2: turn display on
    LCD_ON_CURSOR = 0x02  # DB1: turn cursor on
    LCD_ON_BLINK = 0x01  # DB0: blinking cursor

    LCD_MOVE = 0x10  # DB4: move cursor/display
    LCD_MOVE_DISP = 0x08  # DB3: move display (0-> move cursor)
    LCD_MOVE_RIGHT = 0x04  # DB2: move right (0-> left)

    LCD_FUNCTION = 0x20  # DB5: function set
    LCD_FUNCTION_8BIT = 0x10  # DB4: set 8BIT mode (0->4BIT mode)
    LCD_FUNCTION_2LINES = 0x08  # DB3: two lines (0->one line)
    LCD_FUNCTION_10DOTS = 0x04  # DB2: 5x10 font (0->5x7 font)
    LCD_FUNCTION_RESET = 0x30  # See "Initializing by Instruction" section

    LCD_CGRAM = 0x40  # DB6: set CG RAM address
    LCD_DDRAM = 0x80  # DB7: set DD RAM address

    LCD_RS_CMD = 0
    LCD_RS_DATA = 1

    LCD_RW_WRITE = 0
    LCD_RW_READ = 1

    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        if self.num_lines > 4:
            self.num_lines = 4
        self.num_columns = num_columns
        if self.num_columns > 40:
            self.num_columns = 40
        self.cursor_x = 0
        self.cursor_y = 0
        self.implied_newline = False
        self.backlight = True
        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hide_cursor()
        self.display_on()

    def clear(self):
        # Clears the LCD display and moves the cursor to the top left corner
        try:
            self.hal_write_command(self.LCD_CLR)
            self.hal_write_command(self.LCD_HOME)
        except OSError:
            raise HardwareError('I2C Display not connected. Check pins and address.')
        self.cursor_x = 0
        self.cursor_y = 0

    def show_cursor(self):
        # Causes the cursor to be made visible
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR)

    def hide_cursor(self):
        # Causes the cursor to be hidden
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        # Turns on the cursor, and makes it blink
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR | self.LCD_ON_BLINK)

    def blink_cursor_off(self):
        # Turns on the cursor, and makes it no blink (i.e. be solid)
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY |
                               self.LCD_ON_CURSOR)

    def display_on(self):
        # Turns on (i.e. unblanks) the LCD
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        # Turns off (i.e. blanks) the LCD
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        # Turns the backlight on.

        # This isn't really an LCD command, but some modules have backlight
        # controls, so this allows the hal to pass through the command.
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        # Turns the backlight off.

        # This isn't really an LCD command, but some modules have backlight
        # controls, so this allows the hal to pass through the command.
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        # Moves the cursor position to the indicated position. The cursor
        # position is zero based (i.e. cursor_x == 0 indicates first column).
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40  # Lines 1 & 3 add 0x40
        if cursor_y & 2:  # Lines 2 & 3 add number of columns
            addr += self.num_columns
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        # Writes the indicated character to the LCD at the current cursor
        # position, and advances the cursor by one position.
        if char == '\n':
            if self.implied_newline:
                # self.implied_newline means we advanced due to a wraparound,
                # so if we get a newline right after that we ignore it.
                pass
            else:
                self.cursor_x = self.num_columns
        else:
            self.hal_write_data(ord(char))
            self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y += 1
            self.implied_newline = (char != '\n')
        if self.cursor_y >= self.num_lines:
            self.cursor_y = 0
        self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        # Write the indicated string to the LCD at the current cursor
        # position and advances the cursor position appropriately.
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        # Write a character to one of the 8 CGRAM locations, available
        # as chr(0) through chr(7).
        location &= 0x7
        self.hal_write_command(self.LCD_CGRAM | (location << 3))
        self.hal_sleep_us(40)
        for i in range(8):
            self.hal_write_data(charmap[i])
            self.hal_sleep_us(40)
        self.move_to(self.cursor_x, self.cursor_y)

    def hal_backlight_on(self):
        # Allows the hal layer to turn the backlight on.
        # If desired, a derived HAL class will implement this function.
        pass

    def hal_backlight_off(self):
        # Allows the hal layer to turn the backlight off.
        # If desired, a derived HAL class will implement this function.
        pass

    def hal_write_command(self, cmd):
        # Write a command to the LCD.
        # It is expected that a derived HAL class will implement this function.
        raise NotImplementedError

    def hal_write_data(self, data):
        # Write data to the LCD.
        # It is expected that a derived HAL class will implement this function.
        raise NotImplementedError

    def hal_sleep_us(self, usecs):
        # Sleep for some time (given in microseconds)
        time.sleep_us(usecs)


# PCF8574 pin definitions
MASK_RS = 0x01  # P0
MASK_RW = 0x02  # P1
MASK_E = 0x04  # P2

SHIFT_BACKLIGHT = 3  # P3
SHIFT_DATA = 4  # P4-P7


class I2cLcd(LcdApi):

    # Implements a HD44780 character LCD connected via PCF8574 on I2C

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr

        try:
            self.i2c.writeto(self.i2c_addr, bytes([0]))
        except OSError:
            raise HardwareError("Could not connect to I2C Display. Check the pins and address.")

        utime.sleep_ms(20)  # Allow LCD time to powerup
        # Send reset 3 times
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(5)  # Need to delay at least 4.1 msec
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        utime.sleep_ms(1)
        # Put LCD into 4-bit mode
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        utime.sleep_ms(1)
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)
        gc.collect()

    def hal_write_init_nibble(self, nibble):
        # Writes an initialization nibble to the LCD.
        # This particular function is only used during initialization.
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        gc.collect()

    def hal_backlight_on(self):
        # Allows the hal layer to turn the backlight on
        self.i2c.writeto(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))
        gc.collect()

    def hal_backlight_off(self):
        # Allows the hal layer to turn the backlight off
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        gc.collect()

    def hal_write_command(self, cmd):
        # Write a command to the LCD. Data is latched on the falling edge of E.
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        if cmd <= 3:
            # The home and clear commands require a worst case delay of 4.1 msec
            utime.sleep_ms(5)
        gc.collect()

    def hal_write_data(self, data):
        # Write data to the LCD. Data is latched on the falling edge of E.
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0f) << SHIFT_DATA))
        self.i2c.writeto(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.i2c_addr, bytes([byte]))
        gc.collect()


class I2C_Display(I2cLcd):
    def __init__(self, address=0x27, sda=12, scl=13, perif=0):
        super().__init__(I2C(perif, sda=Pin(sda), scl=Pin(scl), freq=40000), address, 4, 20)
        self.startup()
        self.hide_cursor()

    def startup(self):
        self.blink_cursor_off()
        self.clear()
        # self.putstr("   QuizBox 1.0.0    \n")


# ----------------------------------------------------------------------------------------------------
# TLC5947
# ----------------------------------------------------------------------------------------------------
class TLC5947:
    def __init__(self, num_channels=24, sclk_pin=9, sdin_pin=8, blank_pin=10, xlat_pin=11, pwm_range=4095):
        self.num_channels = num_channels
        self.sclk_pin = sclk_pin
        self.sdin_pin = sdin_pin
        self.blank_pin = blank_pin
        self.xlat_pin = xlat_pin
        self.pwm_range = pwm_range

        # Set up the pins
        self.sclk = Pin(sclk_pin, Pin.OUT)
        self.sdin = Pin(sdin_pin, Pin.OUT)
        self.blank = Pin(blank_pin, Pin.OUT)
        self.blank.value(1)  # Set the BLANK pin high to disable output
        self.xlat = Pin(xlat_pin, Pin.OUT)
        self.xlat.value(0)

        # Set the state changed flag
        self.state_changed = False

        self.blank.value(0)

        # Initialize the channel data to all zeros
        self.channel_data = [0] * self.num_channels
        self.set_all(0)
        self.set_channel(23, 100)
        self.update()

        # for i in range(0, 4095,10):
        #     self.set_all(i)
        #     self.update()
        #     time.sleep(0.001)

    def update(self):
        # Check the state changed flag
        if not self.state_changed:
            return

        # Set the BLANK pin low to enable output
        # self.blank.value(1)

        # Load the channel data
        for value in self.channel_data:
            for i in range(0, 12):
                self.sdin.value((value >> i) & 1)
                self.sclk.value(1)
                self.sclk.value(0)

        # Pulse the XLAT pin to latch the data
        self.xlat.value(1)
        self.xlat.value(0)
        # Set the BLANK pin high to disable output
        # self.blank.value(0)

        # Reset the state changed flag
        self.state_changed = False

    def set_channel(self, channel, value=4095 // 2):
        gamma = 2.5
        value = int(pow(value / 255.0, gamma) * 255.0 + 0.5)
        # Only set the channel data and the state changed flag if the value is different
        if value != self.channel_data[-channel - 1]:
            self.channel_data[-channel - 1] = value
            self.state_changed = True

    def set_led(self, id, inten=.5):
        self.set_channel(id * 3, int(4095 * inten))
        self.set_channel(id * 3 + 1, int(4095 * inten))
        self.set_channel(id * 3 + 2, int(4095 * inten))

    def set_led_rgb(self, led: int, color: Color):

        channels = [led for led in range(led * 3, led * 3 + 3)]

        # Set the values for the red, green, and blue channels of the LED
        for ch, cl in zip(channels, color.getValueAs12Bit()):
            self.set_channel(ch, cl)

    def set_all(self, value: int):
        for ch in range(24):
            self.set_channel(ch, value)
        self.update()

    def set_all_rgb(self, color: Color):
        for led in range(8):
            self.set_led_rgb(led, color)
        self.update()


# ----------------------------------------------------------------------------------------------------
# QuizBoxIO
# ----------------------------------------------------------------------------------------------------
class QuizBox:
    DEBUG_MODE = True
    boxState = 1
    boxStateHasChanged = False
    boxStateChangedExternally = False
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
        def __init__(self, id=14):
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

        self.HOLDING_OVERRIDE = None
        print("Initializing QuizBox\n----------------")
        print("Debug mode: " + "Enabled" if QuizBox.DEBUG_MODE else "Disabled")

        self.tlc = TLC5947()

        self.display = I2C_Display()
        # self.display.putstr("   QuizBox 1.0.0    \n")

        self.reset = self.Reset()

        self.timer = self.Timer()

        self.buzzer = self.Buzzer()

        self.coms = Box2Box()

        self.coms.setState1(lambda holding: (QuizBox.setBoxState(1, external=True), self.overide_holding(holding)))
        self.coms.setState2(lambda: QuizBox.setBoxState(2, external=True))
        self.coms.setState3(lambda x: QuizBox.setBoxState(3, external=True))

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

        if (msg := self.coms.update()) is not None and len(msg) > 0:
            self.display.clear()
            self.display.putstr(msg)
            print(msg)

        # print([(self.quizzers[i].switchpin, self.quizzers[i].switchval) for i  in range(5)])

        # Set state lights to box state
        for led, color in zip([5, 6], self.colors[QuizBox.boxState]):
            self.tlc.set_led_rgb(led, color)
        self.tlc.update()

        if QuizBox.boxStateHasChanged:
            self.boxStateChange()
            QuizBox.boxStateHasChanged = False
            QuizBox.boxStateChangedExternally = False

        if QuizBox.boxState == 1:

            for quizzer in self.quizzers:
                if quizzer.bothread == (True, True):
                    self.tlc.set_led_rgb(quizzer.num - 1, QuizBox.color)
                else:
                    self.tlc.set_led(quizzer.num - 1, 0)
            self.tlc.update()

        elif QuizBox.boxState == 2:

            for quizzer in self.quizzers:
                if quizzer.bothread == (True, True):
                    self.tlc.set_led_rgb(quizzer.num - 1, QuizBox.color)
                    self.tlc.update()
                    self.buzzer.buzz(0.5)
                    QuizBox.setBoxState(3)
                    break

        elif QuizBox.boxState == 3:
            # Set display to show who jumped, show countdown 
            if self.timer.lastWholeSecond >= 0:
                if self.timer.wholeSecondHasChanged():
                    self.display.move_to(0, 1)
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
        if holding is not None:
            self.HOLDING_OVERRIDE = holding

    @staticmethod
    def resetUpdate():
        if QuizBox.boxState == 1:
            QuizBox.setBoxState(2)
        elif QuizBox.boxState == 2:
            QuizBox.setBoxState(1)
        elif QuizBox.boxState == 3:
            QuizBox.setBoxState(1)

        else:
            raise ValueError("ERROR: BoxState should be in [1,2,3]. Setting to 1")

    @staticmethod
    def setBoxState(state, external=False):
        print(f"Setting boxState from {QuizBox.boxState} to {state} ({round(utime.time(), 2)})")

        if state in [1, 2, 3]:
            QuizBox.boxState = state

        QuizBox.boxStateHasChanged = True
        QuizBox.boxStateChangedExternally = external

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

        if not QuizBox.boxStateChangedExternally:
            self.coms.write(f"<S: {QuizBox.boxState}{param}>")
            print(f'sent state f"<S: {QuizBox.boxState}{param}>"')

        if QuizBox.boxState == 3:
            self.timer.startCoutndown(32)


# ----------------------------------------------------------------------------------------------------
# Main Code
# ----------------------------------------------------------------------------------------------------
def main():
    box = QuizBox()

    with open('main_py_checksum.txt', 'r') as f:
        latest_checksum = f.read()

    box.display.clear()

    box.display.putstr(f"{'QuizBox - ' + BRANCH:^20}\n{latest_checksum[:6]:^20}\n")

    sleep(5)

    box.display.clear()

    box.display.putstr("State: Standby")

    while True:
        box.update()


main()
