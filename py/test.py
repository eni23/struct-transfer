#!/usr/bin/env python
import sys
import time
import struct
import serial
import bitstring


try:
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=19200
    )
except:
    print("Opening serial port failed")
    sys.exit(1)
ser.isOpen()
time.sleep(0.5)
print("serial ready")


msg = struct.pack("=B", 4)
ser.write(msg)
dl = ser.read(1)
dlen = struct.unpack("=B",dl)[0]
data = ser.read(dlen)
bitstr = bitstring.BitArray(data)
unpacked = bitstr.unpack('3*uintle:8, 6*uintle:8, 1*uintle:16, 1*uintle:8, 1*uintle:16, 1*uintle:32')

print(unpacked)



ser.close()
