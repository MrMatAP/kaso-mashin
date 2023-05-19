#!/bin/bash

rootdir=$(dirname $0)/..

qemu-system-aarch64 \
  -name qtest \
  -monitor stdio \
  -machine virt \
  -cpu host -accel hvf \
  -smp 2 -m 4096 \
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \
  -display default,show-cursor=on \
  -device virtio-gpu-pci \
  -device virtio-rng-pci \
  -device nec-usb-xhci,id=usb-bus \
  -device usb-kbd,bus=usb-bus.0 \
  -drive if=virtio,file=$rootdir/disks/qtest.qcow2,format=qcow2,cache=writethrough \
  -cdrom $rootdir/isos/ubuntu-22.04.2-live-server-arm64.iso


  #-device ramfb \
  #-bios $rootdir/fw/QEMU_EFI.fd \
  #-drive if=pflash,file=/opt/homebrew/share/qemu/edk2-aarch64-code.fd,format=raw,readonly=on \
  #-drive if=pflash,file=ovmf_vars.fd,format=raw \
  #-drive if=pflash,file=fw/QEMU_EFI.fd,format=raw,readonly=on \
  #-drive if=pflash,file=fw/QEMU_VARS.fd,format=raw \
  #-smbios type=1,serial=ds='nocloud-net;s=http://10.0.2.2:8000' \
  #-device virtio-net-device,netdev=net0 \
  #-netdev user,id=net0 \

