#!/bin/bash

/opt/homebrew/bin/qemu-system-aarch64 \
    -name vnctest \
    -machine virt \
    -cpu host \
    -accel hvf \
    -m 4096 \
    -smp 2 \
    -object rng-random,id=rng0,filename=/dev/urandom \
    -device virtio-rng-pci,rng=rng0 \
    -device virtio-gpu-pci \
    -device nec-usb-xhci,id=usb-bus \
    -device usb-kbd,bus=usb-bus.0 \
    -netdev vmnet-shared,id=net0,start-address=10.3.0.3,end-address=10.3.0.254,subnet-mask=255.255.255.0 \
    -device virtio-net-device,netdev=net0,mac=00:50:56:63:b2:ef \
    -drive if=virtio,file=/Users/imfeldma/var/kaso/instances/vnctest/os.qcow2,format=qcow2,index=0,media=disk \
    -fw_cfg name=opt/org.flatcar-linux/config,file=/Users/imfeldma/var/kaso/instances/vnctest/bootstrap.json \
    -drive if=pflash,file=/Users/imfeldma/var/kaso/instances/vnctest/uefi_code.fd,format=raw,readonly=on \
    -drive if=pflash,file=/Users/imfeldma/var/kaso/instances/vnctest/uefi_vars.fd,format=raw \
    -display vnc=unix:/Users/imfeldma/var/kaso/instances/vnctest/vconsole.sock \
    -chardev socket,id=char0,server=on,wait=off,telnet=on,path=/Users/imfeldma/var/kaso/instances/vnctest/console.sock \
    -serial chardev:char0 \
    -chardev socket,id=char1,server=on,wait=off,path=/Users/imfeldma/var/kaso/instances/vnctest/qmp.sock \
    -mon chardev=char1,mode=control
    
    # Two sockets, one for the mon, the other for serial console
    #-chardev socket,id=char0,server=on,wait=off,telnet=on,path=/Users/imfeldma/var/kaso/instances/vnctest/console.sock \
    #-serial chardev:char0 \
    #-chardev socket,id=char1,server=on,wait=off,path=/Users/imfeldma/var/kaso/instances/vnctest/qmp.sock \
    #-mon chardev=char1,mode=control

    #-nographic \
    #-display cocoa \


    # This works nicely too
    #-chardev socket,id=char0,server=on,wait=off,websocket=on,path=/Users/imfeldma/var/kaso/instances/vnctest/console,mux=on \
    #-mon chardev=char0,mode=readline \
    #-serial chardev:char0 \
    #-serial chardev:char0

    # This successfully redirects the serial console to a socket which can then be connected to
    #-nographic \
    #-chardev socket,id=char0,server=on,wait=on,telnet=on,path=/Users/imfeldma/var/kaso/instances/vnctest/console,mux=on \
    #-mon chardev=char0,mode=readline \
    #-serial chardev:char0 \
    #-serial chardev:char0

    # This successfully redirects the serial console to a port on localhost
    #-nographic \
    #-chardev socket,id=char0,server=on,wait=on,telnet=on,port=5701,host=127.0.0.1,ipv4=on,ipv6=off,mux=on \
    #-mon chardev=char0,mode=readline \
    #-serial chardev:char0 \
    #-serial chardev:char0

    # This redirects the serial console onto the same window we start in
    #-chardev stdio,mux=on,id=char0 \

    # Debug firmware
    #-debugcon file:/Users/imfeldma/var/kaso/instances/vnctest/debuguefi.log \
    #-global isa-debugcon.iobase=0x402

    #-chardev socket,id=console,host=localhost,port=5701,ipv4=on,ipv6=off,nodelay=on,server=on,telnet=on 
    #-display vnc=unix:/Users/imfeldma/var/kaso/instances/vnctest/display.ws,power-control=on,websocket=on
    #-display vnc=localhost:0,power-control=on,websocket=unix:/Users/imfeldma/var/kaso/instances/vnctest/display.ws
