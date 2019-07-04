#!/usr/bin/python
import mmap
import os
import subprocess
import traceback
import optparse
import sys

class Parser:
    def __init__(self, dump_file_dir=None, vmlinux=None, kaslr_offset=None):
        self.page_offset = None
        self.nm = None
        self.gdb = None
        self.objdump = None
        self.output = None
        self.__read_config()
        if (dump_file_dir is not None):
            self.dump_file_dir = dump_file_dir
        if (vmlinux is not None):
            self.vmlinux_path = vmlinux
        self.kaslr_offset = kaslr_offset
        self.ddr_list = []

    def __str__(self):
        self_str = "dump_file_dir = {}\n".format(self.dump_file_dir)
        self_str = self_str + "vmlinux = {}\n".format(self.vmlinux_path)
        if (self.kaslr_offset is not None):
            self_str = self_str + "kaslr = {}\n".format(hex(self.kaslr_offset))
        else:
            self_str = self_str + "kaslr = {}\n".format(("None"))
        self_str = self_str + "gdb = {}\n".format(self.gdb)
        self_str = self_str + "nm = {}\n".format(self.nm)
        self_str = self_str + "objdump = {}\n".format(self.objdump)
        self_str = self_str + "page_offset = {}\n".format(hex(self.page_offset))
        self_str = self_str + "output = {}".format(self.output)
        return self_str

    def __read_config(self):
        f = None
        try:
            f = open("config", "r")
            config = f.read()
            for line in config.split('\n'):
                line = line.replace(" ", "")
                line = line.split("=")
                if (line[0] == "DUMP_FILE_DIR"):
                    self.dump_file_dir = line[1]
                elif(line[0] == "VMLINUX"):
                    self.vmlinux_path = line[1]
                elif(line[0] == "PAGE_OFFSET"):
                    self.page_offset = int(line[1],16)
                elif(line[0] == "GDB"):
                    self.gdb = line[1]
                elif(line[0] == "NM"):
                    self.nm = line[1]
                elif(line[0] == "OBJDUMP"):
                    self.objdump = line[1]
                elif(line[0] == "OUTPUT"):
                    self.output = line[1]
        finally:
            if (f is not None):
                f.close()

    def get_ddr_section_from_load_cmm(self):
        load_cmm_file = None
        try:
            load_cmm_file = open(self.dump_file_dir + os.sep + "load.cmm", "r")
            for l in load_cmm_file.readlines():
                if ("load" in l and "DDRCS" in l):
                    self.ddr_list.append(l.split(" ")[3:5])
            return self.ddr_list
        finally:
            if load_cmm_file is not None:
                load_cmm_file.close()

    def find_kaslr_offset(self,text_offset=0x80000):
        f = None
        mm = None
        try:
            pattern = b"\x56\x69\x72\x74\x75\x61\x6c\x20\x6b\x65\x72\x6e\x65\x6c\x20\x6d\x65"
            find_ddr_list = list(self.ddr_list)
            find_ddr_list.reverse()
            pattern_offset = -1
            print("Searching kaslr offset in DDRSC BIN, it will take long time:");
            if (len(find_ddr_list) <= 0):
                print("Error: DDR BIN list is empty!!! check config and input parameter.")
                return -1
            for l in find_ddr_list:
                ddr_bin = self.dump_file_dir + os.sep + l[0]
                f = open(ddr_bin, "rb")
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                print("Searching {}...".format(l[0]))
                pattern_offset = mm.find(pattern)
                #pattern_offset = 0x3d589c98
                if (pattern_offset >= 0):
                    print("Found Virtual kernel memory layout at {}@{}".format(l[0],hex(pattern_offset)))
                else:
                    continue

                mm.seek(pattern_offset)
                kernel_vaddr_layout_str = str(mm.read(1024))
                kernel_vaddr_layout_str = kernel_vaddr_layout_str.split("\x3c\x35\x3e")
                print(kernel_vaddr_layout_str)
                vmalloc_vaddr = 0
                text_vaddr = 0

                for l in kernel_vaddr_layout_str[:-1]:
                    print(l)
                    if "vmalloc" in l:
                        index_start = l.split("-")[0].find("0x")
                        index_end = l.find(" -")
                        vmalloc_vaddr = l[index_start:index_end]
                        vmalloc_vaddr = int(vmalloc_vaddr,16)
                    elif "text" in l:
                        index_start = l.split("-")[0].find("0x")
                        index_end = l.find(" -")
                        text_vaddr = l[index_start:index_end]
                        text_vaddr = int(text_vaddr, 16)

                kaslr_offset = text_vaddr - vmalloc_vaddr - text_offset
                print("\n\n***************************************************************************************************")
                print("*    Kaslr offset for this dump file is \033[1;31m{}\033[0m, please remember it".format(hex(kaslr_offset)))
                print("*    You can use below command to start this script avoid costing long time to search kaslr offset")
                print("*    python parser.py --kaslr-offset=<kaslr offset>")
                print("***************************************************************************************************\n\n")
                self.kaslr_offset = kaslr_offset
                return kaslr_offset
        except Exception as e:
            traceback.print_exc()
        finally:
            if (f is not None):
                f.close()
            if (mm is not None):
                mm.close()

    class RamdumpParser:
        def __init__(self, parser, ramparser_dir="qc_ramdump_parser/"):
            self.parser = parser
            self.ramparser_dir = ramparser_dir

        def parse_to_file(self):
            cmd = "python {ramparser_dir}/ramparse.py -v {vmlinux} -g {gdb} -n {nm} -j {objdump} -a {dump_file} \
                          -o {out} --force-hardware 8996 --64-bit --page-offset={page_offset} --kaslr-offset={kaslr_offset} \
                          -x".format(ramparser_dir=self.ramparser_dir, vmlinux=self.parser.vmlinux_path,
                                                      gdb=self.parser.gdb, nm=self.parser.nm, objdump=self.parser.objdump,
                                                      dump_file=self.parser.dump_file_dir, out=self.parser.output,
                                                      page_offset=self.parser.page_offset, kaslr_offset=self.parser.kaslr_offset)
            os.system(cmd)
            return 0

    class CrashStarter:
        def __init__(self, parser, crash_path="qcrash/crash64"):
                self.parser = parser
                self.crash_path = crash_path

        def start(self):
            ddr_str=""
            for ddr_info in self.parser.ddr_list:
                print(ddr_info)
                ddr_str = ddr_str + "{ddr_bin}@{ddr_offset},".format(ddr_bin = self.parser.dump_file_dir + os.sep + ddr_info[0], ddr_offset = ddr_info[1])
            ddr_str = ddr_str[:-1]
            vmlinux_path = self.parser.vmlinux_path
            crash_path = self.crash_path
            kaslr_offset = self.parser.kaslr_offset
            cmd = "{crash} {vmlinux} {ddr_str} --kaslr {kaslr_offset}".format(crash=crash_path, vmlinux=vmlinux_path, ddr_str=ddr_str, kaslr_offset=kaslr_offset)
            print(cmd)
            os.system(cmd)

        def start_test(self):
            print(self.parser.ddr_list)

if __name__ == "__main__":
    usage = 'usage: %prog [options to print]. Run with --help for more details'
    option_parser = optparse.OptionParser(usage)
    option_parser.add_option('-v', '--vmlinux', dest='vmlinux', help='vmlinux path')
    option_parser.add_option('', '--kaslr-offset', type='int',
                      dest='kaslr_offset',
                      help='Offset for address space layout randomization')
    option_parser.add_option('-o', '--outdir', dest='outdir', help='Output directory')
    option_parser.add_option('', '--crash', action='store_true',
                      dest='crash', help='Start Crash64 to debug ramdump', default=False)
    option_parser.add_option('', '--ramparse', action='store_true',
                      dest='ramparse', help='Start qcom Linux ramdump parser to parse ramdump to outdir', default=False)
    option_parser.add_option('-d', '--dump-file-dir', dest='dump_file_dir',
                      help='Ramdump file directory path')

    (opts,args) = option_parser.parse_args()
    print(opts, args)
    parser = Parser(dump_file_dir=opts.dump_file_dir, vmlinux=opts.vmlinux, kaslr_offset=opts.kaslr_offset)
    parser.get_ddr_section_from_load_cmm()

    if (parser.ddr_list is None or len(parser.ddr_list) == 0):
        print("Error: Can't get DDRSC bin list")
        sys.exit(-1)

    if (parser.kaslr_offset == None):
        print("Kaslr Offset is not specified, will search it from DDRSC bin.")
        print("If your kernel's KASLR is disabled, plese specify Kaslr Offset to 0.")
        parser.find_kaslr_offset()

    if (parser.kaslr_offset < 0):
        print("Error: KASLR OFFSET is invalid: {}".format(parser.kaslr_offset))
        sys.exit(-1)

    if (opts.ramparse == True):
        r = parser.RamdumpParser(parser)
        r.parse_to_file()

    if (opts.crash == True):
        c = parser.CrashStarter(parser)
        c.start()


## test
#parser = Parser(dump_file_dir = "/home/guoyi/ramdump/Port_COM27/", vmlinux = "/home/guoyi/msm8998/LINUX/android/vmlinux",  kaslr_offset = 0x1eedc00000)
#arser = Parser(dump_file_dir="E:\\ramdump\\1524\\Port_COM12")
#parser.get_ddr_section_from_load_cmm()
#parser.find_kaslr_offset()
#r = parser.RamdumpParser(parser)
#r.parse_to_file()
#parser.get_ddr_section_from_load_cmm()
#ramdup = parser.RamdumpParser()
#crash = parser.CrashStarter(parser)
#crash.start()
