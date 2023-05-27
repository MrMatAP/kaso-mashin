import pathlib

from yaml import dump
try:
    from yaml import CDumper as Dumper      # pylint: disable=unused-import
except ImportError:
    from yaml import Dumper                 # pylint: disable=unused-import

from .renderable import Renderable


class AnsibleInventory(Renderable):
    """
    Manages an instance-specific Ansible inventory.yaml
    """

    def __init__(self, name: str, actual_ip: str):
        self._name = name
        self._actual_ip = actual_ip

    @property
    def name(self) -> str:
        return self._name

    @property
    def actual_ip(self) -> str:
        return self._actual_ip

    @actual_ip.setter
    def actual_ip(self, value: str):
        self._actual_ip = value

    def render(self) -> str:
        return dump({
            'all': {
                'vars': {
                    'ansible_user': 'ansible',
                    'ansible_become_user': 'root',
                    'ansible_become': True
                },
                'hosts': {
                    self.name: {
                        'ansible_host': self.actual_ip
                    }
                }
            }
        })


class AnsibleCfg(Renderable):
    """
    Manages the instance-specific ansible.cfg
    """

    def __init__(self, inventory_path: pathlib.Path):
        self._inventory_path = inventory_path

    @property
    def inventory_path(self) -> pathlib.Path:
        return self._inventory_path

    def render(self):
        return f'''
[defaults]
inventory = {self.inventory_path}
# This is a potential security hole, be sure to keep your playground VM's local. Clearly not for production
host_key_checking = False
        '''


class AnsiblePlaybook(Renderable):
    """
    Manages the base Ansible playbook for postconfiguration
    """

    def render(self) -> str:
        return dump([{
            'name': 'Deploy',
            'hosts': 'all',
            'tasks': [{
                'name': 'Say Hello',
                'ansible.builtin.debug': {
                    'msg': 'Hello World'
                }
            }]
        }])
