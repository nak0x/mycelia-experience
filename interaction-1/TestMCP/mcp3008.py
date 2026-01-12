from machine import Pin

class MCP3008:
    def __init__(self, spi, cs_pin: int):
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT, value=1)

    def read(self, ch: int) -> int:
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
