from machine import SPI, Pin
from time import sleep_ms
from mcp3008 import MCP3008

# VSPI pins from your ESP32 Wrover DevKit pinout
SCK  = 18
MOSI = 23
MISO = 19
CS   = 5

spi = SPI(
    2,  # ESP32: SPI(2) commonly maps to VSPI in MicroPython builds
    baudrate=1_000_000,
    polarity=0,
    phase=0,
    sck=Pin(SCK),
    mosi=Pin(MOSI),
    miso=Pin(MISO),
)

adc = MCP3008(spi, CS)

while True:
    vals = [adc.read(ch) for ch in range(8)]
    print(vals)  # CH0..CH7 as 0..1023
    sleep_ms(200)
