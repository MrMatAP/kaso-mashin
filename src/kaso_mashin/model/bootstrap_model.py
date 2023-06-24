import enum
import ipaddress

from yaml import dump
try:
    from yaml import CDumper as Dumper      # pylint: disable=unused-import
except ImportError:
    from yaml import Dumper                 # pylint: disable=unused-import

from .renderable import Renderable


class BootstrapKind(enum.Enum):
    CI = 'ci'
    CI_DISK = 'ci-disk'
    IGNITION = 'ignition'
    NONE = 'none'


class CIMetaData(Renderable):
    """
    Manages and renders cloud-init Metadata
    """

    def __init__(self, instance_id: str, hostname: str):
        self._instance_id = instance_id
        self._hostname = hostname

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def hostname(self) -> str:
        return self._hostname

    def render(self) -> str:
        return dump({
            'instance-id': f'{self.instance_id}/{self.hostname}',
            'local-hostname': self.hostname
        })


class CINetworkConfig(Renderable):
    """
    Manages cloud-init network-config
    """

    def __init__(self, mac: str, ip4: str, nm4: str, gw4: str, ns4: str):
        self._mac = mac
        self._ip4 = ip4
        self._nm4 = nm4
        self._gw4 = gw4
        self._ns4 = ns4

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def ip4(self) -> str:
        return self._ip4

    @property
    def nm4(self) -> str:
        return self._nm4

    @property
    def gw4(self) -> str:
        return self._gw4

    @property
    def ns4(self) -> str:
        return self._ns4

    def render(self) -> str:

        ip_cidr = ipaddress.IPv4Interface(f'{self.ip4}/{self.nm4}')

        return dump({
            'version': 2,
            'ethernets': {
                'primary0': {
                    'match': {
                        'macaddress': self.mac
                    },
                    'dhcp4': False,
                    'addresses': [ip_cidr.compressed],
                    'gateway4': self.gw4,
                    'nameservers': {
                        'addresses': [self.ns4]
                    },
                    'routes': [{
                        'to': '0.0.0.0/0',
                        'via': self.gw4,
                        'metric': 1
                    }]
                }
            }
        })


class CIUserData(Renderable):
    """
    Manages cloud-init userdata
    """

    def __init__(self, phone_home_url: str, pubkey: str):
        self._pubkey = pubkey
        self._phone_home_url = phone_home_url
        self._locale = 'en_US'
        self._timezone = 'Europe/Zurich'
        self._admin_password = None

    @property
    def admin_password(self):
        return self._admin_password

    @admin_password.setter
    def admin_password(self, value: str):
        self._admin_password = value

    @property
    def pubkey(self) -> str:
        return self._pubkey

    @pubkey.setter
    def pubkey(self, value: str):
        self._pubkey = value

    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, value: str):
        self._locale = value

    @property
    def timezone(self) -> str:
        return self._timezone

    @timezone.setter
    def timezone(self, value: str):
        self._timezone = value

    @property
    def phone_home_url(self) -> str:
        return self._phone_home_url

    def render(self) -> str:
        return '#cloud-config\n---\n' + dump({
            'growpart': {
                'mode': 'auto',
                'devices': ['/']
            },
            'locale': self.locale,
            'timezone': self.timezone,
            'ssh_pwauth': True,
            'users': [
                {
                    'name': 'cloudadmin',
                    'gecos': 'Cloud Admin User',
                    'groups': 'users,admin,wheel',
                    'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                    'shell': '/bin/bash',
                    'lock_passwd': False,
                    'plain_text_passwd': self.admin_password
                },
                {
                    'name': 'ansible',
                    'gecos': 'Ansible Automation User',
                    'groups': 'users,admin,wheel',
                    'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                    'shell': '/bin/bash',
                    'lock_passwd': True,
                    'ssh_authorized_keys': [f'{self.pubkey}']
                }],
            'package_update': True,
            'package_upgrade': True,
            'phone_home': {
                'url': self._phone_home_url,
                'post': [
                    'pub_key_rsa',
                    'instance_id',
                    'hostname',
                    'fqdn'
                ],
                'tries': 5
            }
        })


class CIVendorData(Renderable):
    """
    Manages cloud-init vendor data
    """

    def render(self) -> str:
        return ''

    def __repr__(self):
        return 'VendorData()'
