#!/usr/bin/env python
import sys
import time
import struct
import serial
import pprint
import bitstring



SOURCE_FILE="src/main.cpp"



def structstr_read_file(filename):
    f = open(filename)
    lines = f.readlines()
    f.close();
    structs = []
    tmp_struct = []
    act_struct = False
    for line in lines:
        if line.find("struct ") > -1:
            tmp_struct.append(line)
            act_struct = True
        if act_struct:
            tmp_struct.append(line)
            if line.find("}") > -1:
                act_struct = False
                name = tmp_struct[0].strip().split("struct ")[1].split(" ")[0]
                sdata = {
                    "name": name,
                    "data": tmp_struct[2:-1]
                }
                structs.append(sdata)

                tmp_struct = []
    return structs



def structstr_parse(line_elems):
    unpack_str = ""
    struct_ds = []
    for elem in line_elems:
        cleaned = elem.strip()
        e_type, e_name = cleaned.split(" ")
        e_name = e_name.replace(";","")
        e_len = 1
        bits = 0
        type_str = ""
        e_ptype = ""
        if e_name.find("[") > -1:
            e_len = int( e_name.split("[")[1].split("]")[0] )
            e_name = e_name.split("[")[0]

        if e_type.find("char") > -1:
            type_str = "uintle:8"
            e_bits = e_len * 8
            e_ptype = "char"

        elif e_type == "int":
            e_ptype = "int"
            e_bits = e_len * 16
            type_str = "intle:16"

        elif e_type == "uint":
            e_ptype = "uint"
            e_bits = e_len * 16
            type_str = "uintle:16"

        elif e_type.find("uint") > -1:
            e_ptype = "uint"
            tsize = int( e_type.split("uint")[1].split("_")[0] )
            type_str = "uintle:{0}".format(tsize)
            e_bits = e_len * tsize

        elif e_type.find("int") > -1:
            e_ptype = "int"
            tsize = int( e_type.split("int")[1].split("_")[0] )
            type_str = "intle:{0}".format(tsize)
            e_bits = e_len * tsize

        elif e_type.find("bool") > -1 or e_type.find("boolean") > -1 :
            e_ptype = "bool"
            type_str = "uintle:8"
            e_bits = e_len * 8

        elif e_type.find("float") > -1:
            e_ptype = "float"
            type_str = "floatle:32"
            e_bits = e_len * 32

        e_bitstr = "{0}*{1}".format(e_len, type_str)

        struct_ds.append({
            "name": e_name,
            "len": e_len,
            "type": e_ptype,
            "bits": e_bits,
            "unpack_str": e_bitstr
        });

    return struct_ds



def structstr_get_unpackstr(parsed_arr):
    bs = ""
    for elem in parsed_arr:
        bs+="{0}, ".format(elem["unpack_str"])
    br = bs[:-2]
    return br



def structstr_len(parsed_arr):
    total = 0
    for item in parsed_arr:
        total += item["bits"]
    c_bytes = int(total / 8)
    return c_bytes



def structstr_unpack_data(data, unpack_str, struct_ds):
    bitstr = bitstring.BitArray(data)
    unpacked = bitstr.unpack(unpack_str)
    res = []
    pos = 0
    for item in struct_ds:
        data = []
        ipos = pos
        for i in range(0, int(item["len"]) ):
            i_data = unpacked[ipos + i]

            if item["type"] == "bool":
                i_data = False
                if unpacked[ipos + i] > 0:
                    i_data = True

            if item["type"] == "char":
                if item["len"] - 1 == i: # char null terminator
                    pos += 1
                    continue
                i_data = chr(i_data)

            if item["type"] == "float":
                i_data = float( str(i_data)[:9] )

            data.append(i_data)
            pos += 1

        if item["type"] == "char":
            data = "".join(data)
        elif len(data) == 1:
            data = data[0]

        res.append({
            "name": item["name"],
            "data": data
        })

    return res



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

    structs = structstr_read_file(SOURCE_FILE)
    struct_ds = structstr_parse(structs[0]["data"])
    unpack_str = structstr_get_unpackstr(struct_ds)

    struct_len = structstr_len(struct_ds)

    print("Source file: {0}".format(SOURCE_FILE))
    print("Structname: {0}\n".format(structs[0]["name"]))
    print("Parsed structure:\n{0}\n".format(struct_ds))
    print("Bitstring:\n{0}\n".format(unpack_str))

    print("calculated total:{0}\n".format(struct_len))

    ser = open_serial()
    msg = struct.pack("=B", 4)
    ser.write(msg)
    dl = ser.read(1)
    dlen = struct.unpack("=B",dl)[0]
    data = ser.read(dlen)
    ser.close()

    print("\nRecived total:{0} (calculated={1})\n".format(dlen, struct_len))
    print("Recived data:\n{0}\n".format(data))

    print("result:")
    res = structstr_unpack_data(data, unpack_str, struct_ds)
    for ir in res:
        print( "   {0}: {1}".format(ir["name"], ir["data"]) )



if __name__ == "__main__":
    main()
