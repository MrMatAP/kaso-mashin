# Kaso Mashin

A tool to manage virtual machines on an ARM-based Mac. Kaso Mashin is 'Virtual Machine' in Japanese.

[![Build](https://github.com/MrMatAP/kaso-mashin/actions/workflows/build.yml/badge.svg)](https://github.com/MrMatAP/kaso-mashin/actions/workflows/build.yml)
[![CodeQL](https://github.com/MrMatAP/kaso-mashin/actions/workflows/codeql.yml/badge.svg)](https://github.com/MrMatAP/kaso-mashin/actions/workflows/codeql.yml)

>*SECURITY*: This is not something that you should be running in an open environment at this stage. The current
> implementation implements an *unauthenticated* API on localhost.

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

Kaso Mashin uses

* [qemu](https://www.qemu.org/) for virtualisation. qemu can emulate a great many architectures, but by default we virtualise native aarch64.
* [qcow](https://en.wikipedia.org/wiki/Qcow) for OS images. This has the benefit of minimising the storage footprint of VM instances because we download a cloud-image in qcow2 once to be shared by all of our instances. Only the instance-specific differences are then written to the instance-specific OS image (copy-on-write).
* [cloud-init](https://cloudinit.readthedocs.io/en/latest/index.html#) for initial post-configuration of the instance, just like in a real cloud

## Networking

Apple permits us to host VMs on the usual three kinds of networks:

* Host-only  
  Communication is limited exclusively between the host and the VM. The VM will not be able to communicate with the Internet.
* Shared  
  Communication is limited between the host and the VM but the outbound communication with the Internet is permitted.
* Bridged with the main interface  
  This allows full network communication both in- and outbound.

Your typical choice will be the Shared network. If you wish to bridge the VM to the main network then first be aware
of the security implications involved with that when you're on the go. You also need to be aware that you cannot create
the bridge yourself, Apples vmnet framework insists on doing that for you.

vmnet also insists of the qemu process starting the process to run as root. It would technically be possible for that
not to be a requirement but this requires a special entitlement from Apple that is generally incompatible with open
source software. It is therefore our intention to make this less cumbersome by only having the server component of kaso
mashin run as root while you drive it via the API (typically using the CLI or a future local web UI).

Kaso Mashin precreates three networks, attempting to figure out the situation on your machine (see late_init() in
`src/kaso_mashin/runtime.py`). The host-only and shared networks require setting a DHCP range, which vmnet doesn't
let you turn off, although you can tell Kaso Mashin that your VM ought to have a static IP address. That static IP
address is then set on the VM via the bootstrap process (cloud-init). The networks and DHCP ranges are configurable.

### Images

Kaso Mashin is based on cloud images just like in a real cloud. There are a number of predefined images that it will
just download for you using the `kaso image create` command when using the '--predefined' option but you can also 
browse for them yourself.

We use images in qcow format (copy-on-write). This has the benefit of saving a ton of disk space since every VM will
just store its differences to the master image held in `~/var/kaso/images`. The downside of that is that you have to
be careful not to mess with the downloaded images otherwise all VMs that depend on them will break. Kaso Mashin doesn't
currently check which VMs depend on a given image (it easily could, but we're not there yet) so be careful.

## How to install this

Install [Homebrew](https://brew.sh/) and qemu:

```shell
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
$ brew install qemu
```

Clone this repository and install the Python package. At this stage you will likely want to install this in a virtual
environment. You can also install the Python package into your home directory directly (`pip install --user`) to
avoid having to remember activating the virtual environment before executing `kaso`.

```shell
# Create and activate a virtual environment (optional, but recommended)
$ python -m virtualenv /path/to/virtualenv/kaso-mashin
$ . /path/to/virtualenv/kaso-mashin/bin/activate

# Build and install Kaso Mashin
$ pip install -U /path/to/cloned/sources/dev-requirements.txt
$ python -m build -n --wheel
$ pip install ./dist/*.whl

# Validate whether it worked
$ kaso -h
```

### How to update this

At this point Kaso Mashin is updated from its sources in git. It will be published in the regular Python Packaging Index
by the time it reached a bit more maturity.

```shell
# Navigate to your clone of the Kaso Mashin sources and update
$ git pull

# Activate the virtual environment in which it is currently installed
$ . /path/to/virtualenv/kaso-mashin/bin/activate

# Install and update dependencies, then build and install
$ pip install -U /path/to/cloned/sources/dev-requirements.txt
$ python -m build -n --wheel
$ pip install ./dist/*.whl

# Validate whether it worked
$ kaso -h
```

## Configuration

Kaso Mashin is configurable using a configuration file located in `~/.kaso` (`kaso -h` will tell you where exactly your
local installation expects its configuration file in the description of the -c|--config option). That option will also
permit you to run with a different configuration file.

| Configuration                      | Default       | Description                                                                                          |
|------------------------------------|---------------|------------------------------------------------------------------------------------------------------|
| path                               | ~/var/kaso    | Root path for all images, instances and the sqlite database holding it all together                  |
| default_os_disk_size               | 5G            | The default OS disk size.                                                                            |
| default_phone_home_port            | 10200         | Local port to listen on for instances to phone home. This will be opened on host and shared networks |
| default_server_host                | 127.0.0.1     | IP address on which the Kaso Mashin server will listen on                                            |
| default_server_port                | 8000          | Port on which the Kaso Mashin server will listen on                                                  |
| default_host_network_dhcp4_start   | 172.16.4.10   | First IP address to hand out for the host-only network                                               |
| default_host_network_dhcp4_end     | 172.16.4.254  | Last IP address to hand out for the host-only network                                                |
| default_host_network_cidr          | 172.16.4.0/24 | Host-only network in CIDR notation                                                                   |
| default_shared_network_dhcp4_start | 172.16.5.10   | First IP address to hand out for the shared network                                                  |
| default_shared_network_dhcp4_end   | 172.16.5.254  | Last IP address to hand out for the shared network                                                   |
| default_shared_network_cidr        | 172.16.5.0/24 | Shared network in CIDR notation                                                                      |

## How to use this

### Start the server

Kaso Mashin comes with a single command but both a server and client flavour. **The server must be started
as root** because that is the only way Apples vmnet framework allows us to create networking for our VMs. All 
other commands should be run unprivileged, in a separate terminal.

```shell
$ sudo kaso-server
Password:
[08/25/23 16:12:13] INFO     [kaso_mashin.server.controllers.bootstrap_controller.BootstrapController] Started
                    INFO     [kaso_mashin.server.controllers.os_disk_controller.OsDiskController] Started
                    INFO     [kaso_mashin.server.controllers.identity_controller.IdentityController] Started
                    INFO     [kaso_mashin.server.controllers.image_controller.ImageController] Started
                    INFO     [kaso_mashin.server.controllers.instance_controller.InstanceController] Started
                    INFO     [kaso_mashin.server.controllers.network_controller.NetworkController] Started
                    INFO     [kaso_mashin.server.controllers.phone_home_controller.PhoneHomeController] Started
                    INFO     [kaso_mashin.server.controllers.task_controller.TaskController] Started
                    INFO     [kaso_mashin.server.run] Effective user root
                    INFO     [kaso_mashin.server.run] Owning user imfeldma
                    INFO     [kaso_mashin.server.apis.config_api.ConfigAPI] Started
                    INFO     [kaso_mashin.server.apis.task_api.TaskAPI] Started
                    INFO     [kaso_mashin.server.apis.identity_api.IdentityAPI] Started
                    INFO     [kaso_mashin.server.apis.network_api.NetworkAPI] Started
                    INFO     [kaso_mashin.server.apis.image_api.ImageAPI] Started
                    INFO     [kaso_mashin.server.apis.instance_api.InstanceAPI] Started
INFO:     Started server process [2096]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Create an identity

You will require at least one identity so you can log in to your VMs. The identity can be either an SSH-key based
identity or a password-based identity. 

```shell
# Show currently known identities. This will be empty for a fresh installation.
$ kaso identity list
╭────┬──────┬──────╮
│ ID │ Name │ Kind │
├────┼──────┼──────┤
╰────┴──────┴──────╯

# Show the syntax for creating an identity
$ kaso identity create -h
usage: kaso identity create [-h] -n NAME (--public-key PUBKEY | --password PASSWD) [--gecos GECOS] [--homedir HOMEDIR]
                            [--shell SHELL]

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  The identity name
  --public-key PUBKEY   Path to the SSH public key for public key-type credentials
  --password PASSWD     A password for password-type credentials
  --gecos GECOS         An optional account GECOS to override the default
  --homedir HOMEDIR     An optional home directory to override the default
  --shell SHELL         An optional shell to override the default
  
# Create an identity with a SSH key
$ kaso identity create -n mrmat -k pubkey --public-key /Users/mrmat/.ssh/id_rsa.pub
Created identity with id 1

# Validate
$ kaso identity list
╭────┬───────┬────────────────╮
│ ID │ Name  │ Kind           │
├────┼───────┼────────────────┤
│ 5  │ mrmat │ SSH Public Key │
╰────┴───────┴────────────────╯

# Details
$ kaso identity get --id 5
╭────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Field          │ Value                                                                                                        │
├────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Id             │ 5                                                                                                            │
│ Name           │ mrmat                                                                                                        │
│ Kind           │ SSH Public Key                                                                                               │
│ GECOS          │                                                                                                              │
│ Home Directory │                                                                                                              │
│ Shell          │                                                                                                              │
│ Password       │                                                                                                              │
│ Public Key     │ ssh-rsa                                                                                                      │
│                │ AAAAB some long string                                                                                       │
╰────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

There are still a lot of rough edges with Kaso Mashin at this time and that includes the bootstrapping mechanisms. You 
will likely want to create a password-based identity as a fallback to test problems.

```shell
$ kaso identity create -n debug --password somethingsecret 
Created identity with id 2
```

### Download an image

You will need at least one cloud image for the base OS of your VM. You can upload your own images or download some
of the predefined ones.

> The downloaded images will be held in `~/var/kaso/images` by default. Be sure not to mess with them at all. If you
> modify or move them in any way then the VMs based on the images will break.

```shell
# Show currently known images. This will be empty for a fresh installation.
$ kaso image list
╭────┬──────┬──────╮
│ ID │ Name │ Path │
├────┼──────┼──────┤
╰────┴──────┴──────╯

# Show the syntax for creating an image
$ kaso image create -h
usage: kaso image create [-h] -n NAME
                         (--url URL | --predefined {ubuntu-bionic,ubuntu-focal,ubuntu-jammy,ubuntu-kinetic,ubuntu-lunar,ubuntu-mantic,freebsd-14})
                         [--min-cpu MIN_CPU] [--min-ram MIN_RAM] [--min-space MIN_SPACE]

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  The image name
  --url URL             Provide the URL to the cloud image
  --predefined {ubuntu-bionic,ubuntu-focal,ubuntu-jammy,ubuntu-kinetic,ubuntu-lunar,ubuntu-mantic,freebsd-14}
                        Pick a predefined image
  --min-cpu MIN_CPU     An optional number of minimum vCPUs for this image
  --min-ram MIN_RAM     An optional number of minimum RAM (in MB) for this image
  --min-space MIN_SPACE
                        An optional number of minimum disk space (in MB) for this image
                        
# Download Ubuntu Jammy
$ kaso image create -n jammy --predefined ubuntu-jammy
Download image jammy... ━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  18% 0:01:13

# Validate
$ kaso image get --id 1
╭─────────────────────────┬─────────────────────────────────────────────╮
│ Field                   │ Value                                       │
├─────────────────────────┼─────────────────────────────────────────────┤
│ Id                      │ 1                                           │
│ Name                    │ jammy                                       │
│ Path                    │ /Users/mrmat/var/kaso/images/jammy.qcow2    │
│ Minimum vCPUs           │ 0                                           │
│ Minimum RAM (MB)        │ 0                                           │
│ Minimum Disk Space (MB) │ 0                                           │
╰─────────────────────────┴─────────────────────────────────────────────╯
```

### Verify networks

Kaso Mashin predefines the three kinds of networks Apples vmnet provides you and updates the information of the bridged
network based on what your host is currently running on. It is worthwhile to doublecheck that information before you
create a VM.

```shell
# List the known networks
$ kaso network list
╭────┬─────────────────────────┬─────────╮
│ ID │ Kind                    │ Name    │
├────┼─────────────────────────┼─────────┤
│ 1  │ default_bridged_network │ bridged │
│ 2  │ default_host_network    │ host    │
│ 3  │ default_shared_network  │ shared  │
╰────┴─────────────────────────┴─────────╯

# Get details of the bridged network
$ kaso network get --id 1
╭─────────────────┬─────────────────────────╮
│ Field           │ Value                   │
├─────────────────┼─────────────────────────┤
│ Id              │ 1                       │
│ Name            │ default_bridged_network │
│ Kind            │ bridged                 │
│ Host interface  │ en0                     │
│ Host IPv4       │ 192.168.0.183           │
│ Gateway4        │ 192.168.0.1             │
│ Nameserver4     │ 192.168.0.1             │
│ DHCPv4 Start    │ None                    │
│ DHCPv4 End      │ None                    │
│ Phone home port │ 10200                   │
╰─────────────────┴─────────────────────────╯
```

### Create an instance

You need to know the image id, network id and at least one identity id to create an instance.

```shell
# List instances
$ kaso instance list
╭────┬──────┬──────┬──────────┬────────────╮
│ ID │ Name │ Path │ Image ID │ Network ID │
├────┼──────┼──────┼──────────┼────────────┤
╰────┴──────┴──────┴──────────┴────────────╯

# Show the syntax for creating an instance
$ kaso instance create -h
usage: kaso instance create [-h] -n NAME [--vcpu VCPU] [--ram RAM] [--display {headless,vnc,cocoa}] --network-id NETWORK_ID
                            --image-id IMAGE_ID [--identity-id IDENTITY_ID] [--static-ip4 STATIC_IP4]
                            [-b {ci,ci-disk,ignition,none}] [-s OS_DISK_SIZE]

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  The instance name
  --vcpu VCPU           Number of vCPUs to assign to this instance
  --ram RAM             Amount of RAM in MB to assign to this instance
  --display {headless,vnc,cocoa}
                        How this VM should show its display
  --network-id NETWORK_ID
                        The network id on which this instance should be attached
  --image-id IMAGE_ID   The image id containing the OS of this instance
  --identity-id IDENTITY_ID
                        The identity id permitted to log in to this instance
  --static-ip4 STATIC_IP4
                        An optional static IP address
  -b {ci,ci-disk,ignition,none}, --bootstrapper {ci,ci-disk,ignition,none}
                        The bootstrapper to use for this instance
  -s OS_DISK_SIZE, --size OS_DISK_SIZE
                        OS disk size, defaults to 5G

# Create an instance (note that you may provide --identity-id multiple times
$ kaso instance create -n test --vcpu 2 --ram 2048 --network-id 3 --identity-id 1 --identity 2 --image-id 1 -b ci-disk --display cocoa
Creating instance test... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

# Validate
$ kaso instance get --id 1
╭─────────────────────┬──────────────────────────────────────────────────────╮
│ Field               │ Value                                                │
├─────────────────────┼──────────────────────────────────────────────────────┤
│ Id                  │ 1                                                    │
│ Name                │ test                                                 │
│ Path                │ /Users/imfeldma/var/kaso/instances/test              │
│ MAC                 │ 00:50:56:00:00:01                                    │
│ vCPUs               │ 2                                                    │
│ RAM                 │ 2048                                                 │
│ Display             │ cocoa                                                │
│ Bootstrapper        │ ci-disk                                              │
│ Image ID            │ 1                                                    │
│ Network ID          │ 3                                                    │
│ OS Disk Path        │ /Users/imfeldma/var/kaso/instances/test/os.qcow2     │
│ OS Disk Size        │ 10G                                                  │
│ CI Base Path        │ /Users/imfeldma/var/kaso/instances/test/cloud-init   │
│ CI Disk path        │ /Users/imfeldma/var/kaso/instances/test/ci.img       │
│ VM Script Path      │ /Users/imfeldma/var/kaso/instances/test/vm.sh        │
│ VNC Socket Path     │ /Users/imfeldma/var/kaso/instances/test/vnc.sock     │
│ QMP Socket Path     │ /Users/imfeldma/var/kaso/instances/test/qmp.sock     │
│ Console Socket Path │ /Users/imfeldma/var/kaso/instances/test/console.sock │
╰─────────────────────┴──────────────────────────────────────────────────────╯
```

### Start an instance

You can now start the instance using the `kaso instance start` command. The instance will attempt to phone home a single
time when it is first started. Kaso Mashin will temporarily start a HTTP server to listen on the host IP address of the
chosen network to enable this. 

An additional window will open up depending on your choice of display. You can log in to the instance directly in that
console window or connect via SSH to the IP address the instance finally ended up having. The instance IP address
will be shown in the server log, at least for the first time the instance boots.

You can simply shut down the instance from its console using any of the Linux commands intended for that purpose 
(e.g. `shutdown -h now`) or more roughly stop it via `kaso instance stop`.

## Reference: OpenAPI

Start `kaso server`, then use your preferred web browser to navigate to its [OpenAPI docs](http://localhost:8000/docs)

## Limitations & Improvements

* *SECURITY*: VMs need to invoke Apples vmnet framework to create interfaces on a given bridge. qemu offers privileged helpers on other platforms (i.e. Linux) but does not do so on MacOS. You must therefore start VM's as root, making them execute in privileged context.
* libvirtd has been ported onto MacOS and it could drive VMs in a similar fashion as this solution. It could also deal with (live) migration between more than one Mac, which would be supremely interesting. However, libvirtd continues to attempt creating its own bridge despite configuring a pre-existing bridge for qemu and is therefore not quite ready.

## Hacking

### Tweaking the shell script

It is ultimately the `kaso server` that should start and stop VMs and that is also the reason why it needs to run as root.
In the meantime you are encouraged to tweak the shell script that was created for your VM.

```shell
#!/bin/bash
# This script can be used to manually start the instance it is located in

/opt/homebrew/bin/qemu-system-aarch64 \
  -machine virt \
  -cpu host \
  -accel hvf \
  -smp 2 \
  -m 2048 \
  -bios /opt/homebrew/share/qemu/edk2-aarch64-code.fd \
  -chardev stdio,mux=on,id=char0 \
  -mon chardev=char0,mode=readline \
  -serial chardev:char0 \
  -nographic \
  -device virtio-rng-pci \
  -device nec-usb-xhci,id=usb-bus \
  -device usb-kbd,bus=usb-bus.0 \
  -drive if=virtio,file=/Users/mrmat/var/kaso/instances/test/os.qcow2,format=qcow2,cache=writethrough \
  -smbios type=3,manufacturer=MrMat,version=0,serial=instance_1,asset=test,sku=MrMat \
  -nic vmnet-shared,start-address=172.16.5.10,end-address=172.16.5.254,subnet-mask=255.255.255.0,mac=00:50:56:00:00:01 \
  -drive if=virtio,file=/Users/mrmat/var/kaso/instances/test/ci.img,format=raw
```

### Playing with cloud-init

`kaso-mashin` will generate all the cloud-init files in `INSTANCEDIR/cloud-init`. You can edit these but instances
are using a config drive containing these files by default. 

Edit `INSTANCEDIR/vm.sh` to look for its configuration over the network:

```
    ...
    # Comment out the config drive pointing to cloud-init.img
    #-drive if=virtio,file=/Users/imfeldma/var/kaso/instances/test2/cloud-init.img,format=raw \
    
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
drive `INSTANCEDIR/cloud-init.img` kaso-mashin already created for you and update the files. This will show up as 
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
