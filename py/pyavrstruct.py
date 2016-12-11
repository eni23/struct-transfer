#!/usr/bin/env python

import os
import sys
import time
import struct
import serial
import pprint
import bitstring
import yaml




class StructParser:

    def __init__(self):
        self.filename = False
        self.filemtime = False
        self.source_lines = []
        self.structs_raw = {}
        self.structs = {}
        self.unpack_str = {}
        self.unpacked_raw = {}
        self.item_order = {}


    def load_file(self, filename):
        f = open(filename)
        self.filemtime = int(os.path.getmtime(filename))
        self.filename = filename
        self.source_lines = f.readlines()
        f.close()


    def load_string(self, string):
        self.filename = False
        self.filemtime = False
        self.filename = False
        self.source_lines = string.split("\n")


    def parse(self):
        self.find_structs()
        self.parse_structs()
        self.build_unpack_strings()


    def get_struct(self, struct_name):
        try:
            return self.structs[struct_name]
        except KeyError:
            return False


    def get_struct_raw(self, struct_name):
        try:
            return self.structs_raw[struct_name]
        except KeyError:
            return False


    def get_unpack_str(self, struct_name):
        try:
            return self.unpack_str[struct_name]
        except KeyError:
            return False


    def get_item_order(self, struct_name):
        try:
            return self.item_order[struct_name]
        except KeyError:
            return False


    def get_bytelen(self, struct_name):
        try:
            e_struct = self.structs[struct_name]
        except KeyError:
            return -1
        total = 0
        for item in e_struct:
            total += item["bits"]
            c_bytes = int(total / 8)
        return c_bytes


    def load_yaml(self, yaml_obj):
        self.structs = {}
        self.unpack_str = {}
        self.unpacked_raw = {}
        self.item_order = {}
        for name, data in yaml_obj["struct"].items():
            self.item_order[name] = data["order"]
            self.structs[name] = data["data"]
        self.build_unpack_strings()


    def build_yaml(self, default_flow_style=False):
        yd = {}
        if self.filename:
            yd["file"] = os.path.abspath(self.filename)
            yd["file_mtime"] = self.filemtime
        yd["date"] = int(time.time())
        yd["struct"] = {}
        yi = yd["struct"]
        for name,data in self.structs.items():
            yi[name] = {}
            yi[name]["order"] = self.item_order[name]
            yi[name]["data"] = data

        return yaml.dump(yd,default_flow_style=default_flow_style)


    def build_unpack_strings(self):
        for name,data in self.structs.items():
            e_unpack_str = ""
            for elem in data:
                e_unpack_str += "{0}, ".format( elem["unpack_str"] )
            e_unpack_str = e_unpack_str[:-2]
            self.unpack_str[name] = e_unpack_str


    def find_structs(self):
        self.structs_raw = {}
        tmp_struct = []
        act_struct = False
        for line in self.source_lines:
            if line.find("struct ") > -1:
                tmp_struct.append(line)
                act_struct = True
            if act_struct:
                tmp_struct.append(line)
                if line.find("}") > -1:
                    act_struct = False
                    name = tmp_struct[0].strip().split("struct ")[1].split(" ")[0]
                    self.structs_raw[name] = tmp_struct[2:-1]
                    tmp_struct = []


    def parse_structs(self):
        self.structs = {}
        self.item_order = {}
        for name,data in self.structs_raw.items():
            s_parsed = self.parse_struct_raw(data, name)
            self.structs[name] = s_parsed


    def parse_struct_raw(self, elems_lines, struct_name):
        self.item_order[struct_name] = []
        unpack_str = ""
        struct_ds = []
        for line in elems_lines:
            cleaned = line.strip()
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
            self.item_order[struct_name].append(e_name)

        return struct_ds


    def unpack(self, struct_name, data):
        try:
            struct_ds = self.structs[struct_name]
            unpack_str = self.unpack_str[struct_name]
        except KeyError:
            return False
        bitstr = bitstring.BitArray(data)
        unpacked = bitstr.unpack(unpack_str)
        res = {}
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

            res[item["name"]] = data

        return res








class CacheStruct(StructParser):

    def __init__( self, header_file, cache_dir ):

        super().__init__()

        cache_dir = os.path.abspath(cache_dir)
        fname = os.path.basename(header_file)
        fnoext = ".".join(fname.split(".")[:-1])
        cache_file = "{0}/{1}.scache.yml".format(
            cache_dir,
            fnoext
        )
        self.cache_file = cache_file
        self.header_file = os.path.abspath(header_file)
        if not os.path.isfile(cache_file):
            print("no cache found, build new")
            self.build_cache()
        else:
            print("cache found, reading")
            cache_handle = open(self.cache_file)
            try:
                yml = yaml.load(cache_handle)
            except:
                cache_handle.close()
                self.build_cache()
                return

            cache_handle.close()
            if not yml:
                self.build_cache()
                return

            real_file_mtime = int(os.path.getmtime(self.header_file))
            if real_file_mtime ==  yml["file_mtime"]:
                print("file time matches, load from cache")
                self.load_yaml(yml)
            else:
                print("source timestamp does not match, rebuild cache")
                self.build_cache()


    def build_cache(self):
        print("building cache")
        self.load_file(self.header_file)
        self.parse()
        yml = self.build_yaml()
        cache_handle = open(self.cache_file, 'w')
        cache_handle.write(yml)
        cache_handle.close()
