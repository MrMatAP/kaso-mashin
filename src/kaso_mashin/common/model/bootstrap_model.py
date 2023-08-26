import enum
import ipaddress

from yaml import dump
try:
    from yaml import CDumper as Dumper      # pylint: disable=unused-import
except ImportError:
    from yaml import Dumper                 # pylint: disable=unused-import

from kaso_mashin.server.renderable import Renderable
from .identity_model import IdentityKind
from .instance_model import InstanceModel


class BootstrapKind(enum.Enum):
    CI = 'ci'
    CI_DISK = 'ci-disk'
    IGNITION = 'ignition'
    NONE = 'none'


class CIVendorData(Renderable):
    """
    Manages cloud-init vendor data
    """

    def render(self) -> str:
        return ''

    def __repr__(self):
        return 'VendorData()'


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


class CIUserData(Renderable):
    """
    Manages cloud-init userdata
    """

    def __init__(self, phone_home_url: str, model: InstanceModel):
        self._phone_home_url = phone_home_url
        self._locale = 'en_US'
        self._timezone = 'Europe/Zurich'
        self._model = model

    @property
    def phone_home_url(self) -> str:
        return self._phone_home_url

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
    def model(self):
        return self._model

    def render(self) -> str:
        userdata = {
            'growpart': {
                'mode': 'auto',
                'devices': ['/']
            },
            'locale': self.locale,
            'timezone': self.timezone,
            'ssh_pwauth': True,
            'package_update': True,
            'package_upgrade': True,
            'phone_home': {
                'url': self.phone_home_url,
                'post': 'all',
                'tries': 5
            },
            'final': '\n'.join(['kaso-mashin bootstrap finished',
                                'version:    $version',
                                'timestamp:  $timestamp',
                                'datasource: $datasource',
                                'uptime:     $uptime']),
            'users': []
        }
        for identity in self.model.identities:
            account = {
                'name': identity.name,
                'groups': 'users,admin,wheel',
                'sudo': 'ALL=(ALL) NOPASSWD:ALL'
            }
            if identity.gecos:
                account['gecos'] = identity.gecos
            if identity.homedir:
                account['homedir'] = identity.homedir
            if identity.shell:
                account['shell'] = identity.shell
            if identity.kind == IdentityKind.PUBKEY:
                account['ssh_authorized_keys'] = [f'{identity.pubkey}']
                account['lock_passwd'] = True
            else:
                account['hashed_passwd'] = identity.passwd
                account['lock_passwd'] = False
            userdata['users'].append(account)
        return '#cloud-config\n---\n' + dump(userdata)


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



