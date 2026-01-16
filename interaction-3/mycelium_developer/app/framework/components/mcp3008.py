from machine import SPI, Pin
import time
from framework.app import App

class Chanel:
    def __init__(self, pin, name, on_value=None) -> None:
        self.pin = pin
        self.name = name
        self.on_value = on_value

    def update(self, value):
        if self.on_value is not None:
            self.on_value(value)

class MCP3008:
    def __init__(
            self,
            chanels=[],
            cs=5,
            sck=18,
            mosi=23,
            miso=19,
            vspi=2,
            bauds=1_000_000,
            polarity=0,
            phase=0,
            read_delay=20) -> None:

        self.spi = SPI(
            vspi,
            baudrate=bauds,
            polarity=polarity,
            phase=phase,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso),
        )
        self.cs = Pin(cs, Pin.OUT, value=1)
        self.chanels = chanels
        self.last_read = time.ticks_ms()
        self.read_delay = read_delay
        App().update.append(self.update)

    def update(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_read) >= self.read_delay:
            self.last_read = now
            for ch in self.chanels:
                ch.update(self._read(ch.pin))


    def _read(self, ch: int) -> int:
        if not 0 <= ch <= 7:
            raise ValueError("channel must be 0..7")

        tx = bytearray(3)
        rx = bytearray(3)
        tx[0] = 0x01
        tx[1] = 0x80 | (ch << 4)  # single-ended + channel
        tx[2] = 0x00

        self.cs.value(0)
        self.spi.write_readinto(tx, rx)
        self.cs.value(1)

        return ((rx[1] & 0x03) << 8) | rx[2]  # 0..1023
