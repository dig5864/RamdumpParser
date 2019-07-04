#!/bin/bash
gdb=/home/guoyi/share/aarch64-linux-android-4.9-master/bin/aarch64-linux-android-gdb
nm=/home/guoyi/share/aarch64-linux-android-4.9-master/bin/aarch64-linux-android-nm
objdump=/home/guoyi/share/aarch64-linux-android-4.9-master/bin/aarch64-linux-android-objdump
out=out
if [ $1 == "1" ]; then
    vmlinux=/home/guoyi/msm8998/LINUX/android/vmlinux
    dump_dir=~/ramdump/Port_COM27/
    python ramparse.py -v $vmlinux -g $gdb -n $nm -j $objdump -a $dump_dir -o $out --force-hardware 8996 --64-bit  --page-offset=0xffffff8008000000 --kaslr-offset=0x1133600000 -x
else
    vmlinux=/home/guoyi/msm8998/LINUX/android/vmlinux_backup1
    dump_dir=~/ramdump/backup1_failed/
    python ramparse.py -v $vmlinux -g $gdb -n $nm -j $objdump -a $dump_dir -o $out --force-hardware 8996 --64-bit  --page-offset=0xffffff8008000000 --kaslr-offset=0
fi

#python ramparse.py -v $vmlinux -g $gdb -n $nm -j $objdump -a $dump_dir -o $out --force-hardware 8996 --64-bit --kaslr-offset=0x86006d0 --page-offset=0xffffff8008000000
#python ramparse.py -v $vmlinux -g $gdb -n $nm -j $objdump -e $dump_dir/DDRCS0_0.BIN 0x40000000  0xbfffffff -o $out --force-hardware 8996 --64-bit --phys-offset=0x40000000 -x
