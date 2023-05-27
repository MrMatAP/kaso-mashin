# MrMat :: Playground

An experimental but efficient way to spin up virtual machines on an ARM-based MAC.

>*SECURITY*: We use [cloud-init](https://cloudinit.readthedocs.io/en/latest/index.html) to perform initial
> postconfiguration of the instances The default configuration will create two users, 'ansible' using an SSH 
> authorized key and 'cloudadmin' with an admin password you specify during the initial creation of the cloud
> playground. The 'cloudadmin' password is currently stored as clear-text in the cloud-init configuration and 
> in the cloud database. VMs are consequently not meant for production or in any situation where they directly
> expose themselves towards an untrusted environment.

## Background

Apple has become extremely restrictive on what you can do on their hardware and these days all but prohibits anyone
to use or create kernel extensions. This impacts virtualisation software as well as more creative network 
configurations. I have a Mac Studio with tons of RAM and plenty of cores, so it's annoying.

Commercial vendor software (VMWare, Parallels) are equally impacted by this. They're just shiny frontends for
Apples [Hypervisor](https://developer.apple.com/documentation/hypervisor) and [vmnet](https://developer.apple.com/documentation/vmnet)
frameworks, which is all that Apple allows us to have. Both are limited just as anyone else and Parallels is even
subscription-based. The free [UTM](https://mac.getutm.app/) is just as nice a frontend as the others.
So is [VirtualBox](https://www.virtualbox.org/), but it remains in beta.

If you're looking for convenience and are happy with what the above frontends provide then stop reading now. But while
we must grudgingly accept the Apple-imposed constraints, we can be a lot better for more-indepth technical configuration.
This is what this playground is about.

## Features

* We use [qemu](https://www.qemu.org/) for virtualisation. qemu can emulate a great many architectures, but by default we virtualise native aarch64.
* We use [qcow](https://en.wikipedia.org/wiki/Qcow) for OS images. This has the benefit of minimising the storage footprint of VM instances because we download a cloud-image in qcow2 once to be shared by all of our instances. Only the instance-specific differences are then written to the instance-specific OS image (copy-on-write).
* We use [cloud-init](https://cloudinit.readthedocs.io/en/latest/index.html#) for initial post-configuration of the instance, just like in a real cloud
* We use [Ansible](https://docs.ansible.com/) for further post-configuration. By default we only minimally post-configure, but we expect further customisation of the 1..n VM's you create is likely going to happen via Ansible. So everything is ready for you to do this with minimal effort.

## Prerequisites

### Networking

Apple permits us to create VLANs and Bridges using System Settings -> Network. The bridges you can create there are of 
no use since qemu or libvirtd do not recognise them and vmnet does not simply permit these client tools to create 
virtual interfaces on them. It is possible to run qemu VM's with an entirely user-space network stack, thereby making
these VM's unprivileged. But the downside of doing this is that you must forward individual ports to a specific machine,
it's not a 'real network'. See the Hacking appendix for an example.

To model some more real-world scenarios and have more flexibility in what you expose from these VM's, I recommend
you create a dedicated VLAN. That VLAN should currently be routed to the Internet so your router must be aware of
it. There can be DHCP on that VLAN, but this is not strictly required.

### Software 

Install [Homebrew](https://brew.sh/) and qemu:

```shell
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
$ brew install qemu
```

Clone this repository and install the Python package:

```shell
python -m build -n --wheel
pip install --user ./dist/*.whl
```

## How to use this

Create a cloud playground (one time. Well, multiple times if you want to have multiple directories using -p)

```shell
$ mrmat-playground \
  -p /Users/login/var/mrmat-playground \   # path to the cloud's home directory. You may wish to exclude this from backup
  cloud create \
  -n mrmat-playground \                       # Arbitrary name
  --admin-password verysecret \               # Password for the 'cloudadmin' console user
  --ssh-public-key /Users/login/.ssh/id_rsa.pub \   # Path to a public key
  --host-if vlan1 \                           # Name of the interface you wish to run your instances on
  --host-ip4 172.16.3.10 \                    # Host IP address
  --host-nm4 255.255.255.0 \                  # Host netmask
  --host-gw4 172.16.3.1 \                     # Host Gateway
  --host-ns4 172.16.3.1                       # Host nameserver
```

Download an image, see 'image download -h' for the available images:

```shell
$ mrmat-playground \
  -p /Users/login/var/mrmat-playground \   # path to the cloud's home directory. ~/var/mrmat-playground is the default
  image download \
  -n ubuntu-jammy                          # Name of the cloud image to download
```

Create an instance:

```shell
$ mrmat-playground \
  instance create \
  -n test \                                 # Name of the instance
  --ip 172.16.3.5                           # Static IP address of the instance
```

Open a separate terminal and start the instance. You must do this with elevated privileges (see Limitations & Improvements):

```shell
$ sudo INSTANCEDIR/vm.sh
.... boots in the same terminal
```

The instance will now postconfigure itself, once it's done with its cloud initialisation it will phone home to the small
webswerver mrmat-playground has spun up. This will then execute a bit of Ansible to further postconfigure the instance.
To shut down the instance, you can just close the separate window which will kill the qemu process. A more graceful way
to do that without logging in is to hit `Ctrl-A C`, which will get you to [qemu's monitor interface](https://qemu-project.gitlab.io/qemu/system/monitor.html).
Type 'quit' to shut things down.

It is obviously more graceful to log in using the 'cloudadmin' user and then `shutdown -h now`. The password for the
cloudadmin user is the same you provided when you created the cloud. If you forgot what that was, look at the cloud
table in `cloud.sqlite3`. You can also log in as 'ansible' using the SSH key you provided:

```shell
$ eval $(ssh-agent)
$ ssh-add
... type your passphrase
$ cd INSTANCEDIR
$ ansible-playbook -i inventory.yaml deploy.yaml
```

`deploy.yaml`, `inventory.yaml` and `ansible.cfg` are generated for you by mrmat-playground. These are executed once
the VM has phoned home. They are deliberately light because you might not want to do Ansible, but set things up 
appropriately when you do. The actual IP address of the VM is placed in `inventory.yaml`, so it does not stricly
need to be known by DNS, although a future improvement would definitely be to update a DNS server with it. `ansible.cfg`
is configured to turn off strict host key checking. A future improvement would definitely be to record the host key
and update your known hosts with it (the host key comes along when the VM phones home). To customise the Ansible, simply 
hack on the files that were generated. You can create a roles directory in INSTANCEDIR and treat the same directory 
as your Ansible root. 

At this point, you do no longer need the `mrmat-playground` script for that instance. From here on, you can just boot
it up by running `INSTANCEDIR/vm.sh`.

## Limitations & Improvements

* *SECURITY*: Creating a cloud-playground involves setting some `--admin-password` for the 'cloudadmin' user. That password is relayed via cloud-init in plain-text. There should be an option for this not to happen, and if it does it should be sha512 hashed.
* *SECURITY*: VMs need to invoke Apples vmnet framework to create interfaces on a given bridge. qemu offers privileged helpers on other platforms (i.e. Linux) but does not do so on MacOS. You must therefore start VM's as root, making them execute in privileged context.
* libvirtd has been ported onto MacOS and it could drive VMs in a similar fashion as this solution. It could also deal with (live) migration between more than one Mac, which would be supremely interesting. However, libvirtd continues to attempt creating its own bridge despite configuring a pre-existing bridge for qemu and is therefore not quite ready.
* Apple permits us to create VLANs and Bridges using System Settings -> Network. The bridges you can create there are of no use since qemu or libvirtd do not recognise them and vmnet does not simply permit these client tools to create virtual interfaces on them.
* mrmat-playground currently configures VMs to have a static IP address, because we'll want to use it for creating k8s clusters eventually. This is truly not required though and we already have the mechanism to pick up what the IP address obtained via DHCP actually was, then write into some DNS server configuration.
* mrmat-playground will currently listen on hardcoded port 10300 for VMs to phone home. 
* *SECURITY*: ansible.cfg explicitly turns off strict host key checking

## Hacking

### Running VM's with user-space networking

```shell
#!/bin/bash

rootdir=$(dirname $0)/..
name=cloudboot

if [ ! -f $rootdir/disks/$name.qcow2 ]; then
  cp $rootdir/var/isos/jammy-server-cloudimg-arm64.qcow2 $rootdir/disks/$name.qcow2
fi

qemu-system-aarch64 \
  -name $name \
  -monitor stdio \
  -machine virt \
  -cpu host -accel hvf \
  -smp 2 -m 4096 \
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \
  -display default,show-cursor=on \
  -netdev user,id=net.0,hostname=$name,domainname=covenant.mrmat.org,hostfwd=tcp:127.0.0.1:10022-:22 \
  -device virtio-gpu-pci \
  -device virtio-rng-pci \
  -device nec-usb-xhci,id=usb-bus \
  -device usb-kbd,bus=usb-bus.0 \
  -device virtio-net-pci,netdev=net.0 \
  -drive if=virtio,file=$rootdir/disks/$name.qcow2,format=qcow2,cache=writethrough \
  -smbios type=3,manufacturer=MrMat,version=0,serial=${name}0,asset=${name}0,sku=cloudboot \
  -smbios type=1,serial=ds='nocloud-net;s=http://10.0.2.2:8000/__dmi.chassis-asset-tag__'
```

This script will create a VM with a network device in user-space with id 'net.0' and forward all SSH traffic
from 127.0.0.1:10022 to port 22 of that VM. The hostname and domainname options configure the implicit DHCP
server running on that user-space network. The network is 10.0.2.0/24 by default, with the host listening on
10.0.2.2. The last line of the script tells the VM to obtain its cloud-init configuration from a webserver
listening on the host address on port 8000.

```
  ...
  -netdev user,id=net.0,hostname=$name,domainname=covenant.mrmat.org,hostfwd=tcp:127.0.0.1:10022-:22 \
  -device virtio-net-pci,netdev=net.0 \
  ...
```

### Playing with cloud-init

`mrmat-playground` will generate all the cloud-init files in `INSTANCEDIR/cloud-init`. You can edit these but instances
are using a config drive containing these files by default. 

Edit `INSTANCEDIR/vm.sh` to look for its configuration over the network:

```
    ...
    # Comment out the config drive pointing to cloud-init.img
    #-drive if=virtio,file=/Users/imfeldma/var/mrmat-playground/instances/test2/cloud-init.img,format=raw \
    
    # Add a lookup over the network
    -smbios type=1,serial=ds='nocloud-net;s=http://172.16.3.10:8000/__dmi.chassis-asset-tag__'
```

You will need to replace 172.16.3.10 with the IP address of the host interface of the VLAN you configured to start the
VMs on. The simplest way to make the cloud-init config files available over the network is to start Python to serve them
from the `INSTANCEDIR/cloud-init` directory:

```shell
$ cd INSTANCEDIR/cloud-init
$ python -m http.server --directory .
```

You can now happily hack on the cloud-init files and see if/when/how the VM comes to pick them up. If you wish to have
a more centrally managed webserver do this then you will need to have a way for distinguishing which VM comes along.
This can be configured in `INSTANCEDIR/vm.sh` where the URI it picks up its cloud-init from can contain various [placeholders](https://cloudinit.readthedocs.io/en/latest/reference/datasources/nocloud.html#dmi-specific-kernel-commandline).
In the example above, the URI will have the asset tag appended. The asset tag is configured in the smbios type=3 configuration
you'll find in the generated `INSTANCEDIR/vm.sh` and set to the machine name by default.

It is not possible to include networking configuration this way for obvious chicken & egg reasons. If you need to configure
the network of the VM then you must update the config drive you commented out earlier. You can just doubleclick the config
drive `INSTANCEDIR/cloud-init.img` mrmat-playground already created for you and update the files. This will show up as 
a 'CIDATA' drive on your desktop. Be sure to eject that drive once you updated its content.

You can also automate the creation of such a config drive using the following commands:

```shell
$ dd if=/dev/zero of=/path/to/custom-cloud-init.img bs=512 count=2880
$ hdiutil attach -nomount /path/to/custom-cloud-init.img
<prints out kernel device node>
$ diskutil eraseVolume MS-DOS CIDATA /path/to/kernel/device/node
$ cp INSTANCEDIR/cloud-init /Volumes/CIDATA/
$ diskutil eject /path/to/kernel/device/node
```

### Playing with qcow2

`images` holds the backing stores for `INSTANCEDIR/os.qcow2`. **Do not delete or modify the backing store, as that will break
all VMs that rely on it**. 

If you wish to 'reset' a VM then delete `INSTANCEDIR/os.qcow2`. You can recreate it using the following commands:

```shell
$ qemu-img create -f qcow2 -b /path/to/images/whatever.qcow2 -F qcow2 INSTANCEDIR/os.qcow2
$ qemu-img resize INSTANCEDIR/os.qcow2 DESIRED_SIZE
```

### Playing with the HW

qemu has whole lot of interesting devices that you can add to your VM. You can see what devices it supports by running
the following command, and get specific help for a given device as well:

```shell
$ qemu-system-aarch64 -device help
... all devices it knows about

$ qemu-system-aarch64 -device sst25vf032b,help
sst25vf032b options:
  drive=<str>            - Node name or ID of a block device to use as a backend
  nonvolatile-cfg=<uint32> -  (default: 36863)
  spansion-cr1nv=<uint8> -  (default: 0)
  spansion-cr2nv=<uint8> -  (default: 8)
  spansion-cr3nv=<uint8> -  (default: 2)
  spansion-cr4nv=<uint8> -  (default: 16)
  write-enable=<bool>    -  (default: false)
```

To add a piece of emulated or virtualised hardware to your VM, simply add it to `INSTANCEDIR/vm.sh`.
