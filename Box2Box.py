from machine import Pin, UART
from time import sleep
import re

# Messages should be instructions.
b"<S: 1>"
b"<S: 1, Holding>"
b"<S: 2>"
b"<S: 3, Timer: {}>"

class Box2Box:
    LATEST_MSG_FROM : None | UART = None


    class Message:
        def __init__(self, msg: bytes | None, sender: UART) -> None:
            if msg == None:
                self.msg = b""
            else:
                self.msg = msg

            self.sender = sender

        @staticmethod
        def init_from_str(msg: str, sender: UART):
            return Box2Box.Message(msg.encode("utf-8"), sender)
        
        def getMsg(self):
            if self.msg == None:
                return None

            message = str(self)
            latest_msg = ""

            for ind in range(len(message)):
                if message[-(ind+1)] == "<":
                    latest_msg = message[-ind:-1]
                    break
            else:
                return None
                


            if latest_msg == "S: 1" or latest_msg == "S: 1, Holding" or latest_msg == "S: 2" or latest_msg.startswith("S: 3, Timer: "):
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
    COM1 = [0,1,2,3]
    COM2 = [4,5,6,7]

    def __init__(self) -> None:
        self.com_left = UART(0, 9600, tx=Pin(Box2Box.COM1[0]), rx=Pin(Box2Box.COM1[1]))
        self.com_right = UART(1, 9600, tx=Pin(Box2Box.COM2[0]), rx=Pin(Box2Box.COM2[1]))

        # lambda functions:
        self._state1 = lambda holding: None
        self._state2 = lambda: None
        self._state3 = lambda x : None

    def update(self) -> str | None:
        msg = self.getInput()
        if msg:
            return self.parseInput(msg)

    def getInput(self):
        messages = [self.Message(self.com_left.read(), self.com_left), self.Message(self.com_right.read(), self.com_right)]

        for msg in messages:
            if msg.msg:
                return msg

    def parseInput(self, message: Message) -> None | str:
        msg = message.getMsg()


        if msg == None:
            return

        self.write(msg, self.getOtherCom(message.sender))
        
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



def main():
    b2b = Box2Box()

if __name__ == '__main__':
    main()
