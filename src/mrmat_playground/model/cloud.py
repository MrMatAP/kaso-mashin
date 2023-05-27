import typing
import pathlib
import netifaces
import sqlite3

from mrmat_playground import console, PlaygroundException


class Cloud:
    """
    An implementation of a local cloud playground
    """

    def __init__(self, path: str = None):
        self._path = pathlib.Path(path)
        self._name = None
        self._admin_password = None
        self._public_key_path = None
        self._public_key = None
        self._host_if = None
        self._host_ip4 = None
        self._host_nm4 = None
        self._host_gw4 = None
        self._host_ns4 = None
        self._ph_port = 10300
        self._db_path = self.path.joinpath('cloud.sqlite3')
        self._instances_path = self.path.joinpath('instances')
        self._images_path = self.path.joinpath('images')

    @property
    def path(self) -> pathlib.Path:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def admin_password(self) -> str:
        return self._admin_password

    @admin_password.setter
    def admin_password(self, value: str):
        self._admin_password = value

    @property
    def public_key_path(self) -> pathlib.Path:
        return self._public_key_path

    @public_key_path.setter
    def public_key_path(self, value: str):
        p = pathlib.Path(value)
        if not p.exists():
            raise PlaygroundException(status=400, msg=f'Public key at {value} does not exist')
        self._public_key_path = p
        pubkey = p.read_text(encoding='UTF-8').strip().split(' ')
        self._public_key = f'{pubkey[0]} {pubkey[1]}'

    @property
    def public_key(self) -> str:
        return self._public_key

    @property
    def host_if(self) -> str:
        return self._host_if

    @host_if.setter
    def host_if(self, value: str):
        if value not in netifaces.interfaces():
            raise PlaygroundException(status=400, msg=f'Host interface {value} does not exist')
        self._host_if = value

    @property
    def host_ip4(self) -> str:
        return self._host_ip4

    @host_ip4.setter
    def host_ip4(self, value: str):
        self._host_ip4 = value

    @property
    def host_nm4(self) -> str:
        return self._host_nm4

    @host_nm4.setter
    def host_nm4(self, value: str):
        self._host_nm4 = value

    @property
    def host_gw4(self) -> str:
        return self._host_gw4

    @host_gw4.setter
    def host_gw4(self, value: str):
        self._host_gw4 = value

    @property
    def host_ns4(self) -> str:
        return self._host_ns4

    @host_ns4.setter
    def host_ns4(self, value: str):
        self._host_ns4 = value

    @property
    def db_path(self) -> pathlib.Path:
        return self._db_path

    @property
    def instances_path(self) -> pathlib.Path:
        return self._instances_path

    @property
    def images_path(self) -> pathlib.Path:
        return self._images_path

    @property
    def ph_port(self) -> int:
        return self._ph_port

    @ph_port.setter
    def ph_port(self, value: int):
        self._ph_port = value

    def create(self):
        if not self.path:
            raise PlaygroundException(status=400, msg='The cloud playground must have a path')
        if not self.name:
            raise PlaygroundException(status=400, msg='The cloud playground must have a name')
        if self.path.exists():
            raise PlaygroundException(status=400, msg=f'Cloud playground directory at {self.path} already exists. '
                                                      f'Remove it first')
        self.path.mkdir(parents=True, exist_ok=True)
        self.path.joinpath('instances').mkdir(exist_ok=True)
        self.path.joinpath('images').mkdir(exist_ok=True)

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS cloud(name, admin_password, public_key_path)')
        cur.execute('INSERT INTO cloud VALUES (?, ?, ?)',
                    (self.name, self.admin_password, str(self.public_key_path)))
        cur.execute('CREATE TABLE IF NOT EXISTS network(host_if, host_ip4, host_nm4, host_gw4, host_ns4, ph_port)')
        cur.execute('INSERT INTO network VALUES (?, ?, ?, ?, ?, ?)',
                    (self.host_if, self.host_ip4, self.host_nm4, self.host_gw4, self.host_ns4, self._ph_port))
        cur.execute('CREATE TABLE IF NOT EXISTS instances(instance_id INTEGER PRIMARY KEY AUTOINCREMENT,'
                    ' name, path, mac)')
        con.commit()
        cur.close()
        con.close()
        console.log(f'Created cloud playground {self.name} at path {self.path}')
        return 0

    def register_instance(self, name: str, path: pathlib.Path) -> typing.Tuple:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('INSERT INTO instances (name, path) VALUES (?, ?)', (name, str(path)))
        con.commit()
        res = cur.execute('SELECT instance_id FROM instances WHERE name = ? AND path = ?', (name, str(path)))
        instance_id = res.fetchone()[0]

        # We start with 00:00:5e, then simply add the instance_id integer
        mac_raw = str(hex(int(0x5056000000) + instance_id)).removeprefix('0x').zfill(12)
        mac = f'{mac_raw[0:2]}:{mac_raw[2:4]}:{mac_raw[4:6]}:{mac_raw[6:8]}:{mac_raw[8:10]}:{mac_raw[10:12]}'

        cur.execute('UPDATE instances SET mac = ? WHERE instance_id = ?', ( mac, instance_id ))
        con.commit()
        cur.close()
        con.close()
        console.log(f'Created MAC address {mac} for instance_id {instance_id}')
        return f'instance{instance_id}', mac

    def load(self):
        if not self.db_path.exists():
            raise PlaygroundException(status=400, msg=f'Cloud playground database at {self.db_path} does not exist')
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        res = cur.execute('SELECT name, admin_password, public_key_path FROM cloud')
        self.name, self.admin_password, self.public_key_path = res.fetchone()
        res = cur.execute('SELECT host_if, host_ip4, host_nm4, host_gw4, host_ns4, ph_port FROM network')
        self.host_if, self.host_ip4, self.host_nm4, self.host_gw4, self.host_ns4, self.ph_port = res.fetchone()
        cur.close()
        con.close()
        console.log(f'Loaded cloud playground {self.name} from path {self.path}')
