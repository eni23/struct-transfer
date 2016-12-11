#!/usr/bin/env python
import sys
import time
import serial
import pyavrstruct
from pprint import pprint


STRUCT_NAME="TTEST"


def open_serial():
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
    return ser


def main():

    structs = pyavrstruct.CacheStruct( "../src/main.cpp", "." )

    s_ord = structs.get_item_order( STRUCT_NAME )
    s_len = structs.get_bytelen( STRUCT_NAME )

    ser = open_serial()
    ser.write([51])
    time.sleep(0.05)
    data = ser.read(s_len)
    ser.close()

    print("Recived data:\n{0}\n\nresult:".format(data))

    res = structs.unpack( STRUCT_NAME, data )
    for var_name in s_ord:
        print( "  {0}: {1}".format( var_name, res[var_name]) )



if __name__ == "__main__":
    main()
