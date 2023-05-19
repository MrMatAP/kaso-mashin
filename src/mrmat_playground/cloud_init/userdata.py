class UserData:
    """
    Manages cloud-init userdata
    """

    def __init__(self, pubkey: str):
        self._pubkey = pubkey

    def render(self) -> str:
        return f'''
#cloud-config
---
growpart:
  mode: auto
  devices: ['/']
locale: en_US
timezone: Europe/Zurich
ssh_pwauth: false
users:
- name: ansible
  gecos: Ansible Automation User
  groups: users,admin,wheel
  sudo: ALL=(ALL) NOPASSWD:ALL
  shell: /bin/bash
  lock_passwd: true
  ssh_authorized_keys:
  - '{self._pubkey}'
package_update: true
package_upgrade: false
packages:
- net-tools
phone_home:
  url: http://172.16.3.10:10300/$INSTANCE_ID/
  post:
  - pub_key_dsa
  - pub_key_rsa
  - pub_key_ecdsa
  - pub_key_ed25519
  - instance_id
  - hostname
  - fqdn
  tries: 5
final_message: |
  Welcome to MrMat - Playground
  Version: $version
  Timestamp: $timestamp
  Datasource: $datasource
  Uptime: $uptime
        '''

    def __repr__(self):
        return f'Userdata(pubkey={self._pubkey})'
