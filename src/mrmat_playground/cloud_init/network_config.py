class NetworkConfig:
    """
    Manages cloud-init network-config
    """

    def __init__(self, mac: str, ip: str, gw: str, ns: str):
        self._mac = mac
        self._ip = ip
        self._gw = gw
        self._ns = ns

    def render(self) -> str:
        return f'''
version: 2
ethernets:
  primary0:
    match:
      macaddress: '{self._mac}'
    dhcp4: false
    addresses:
      - {self._ip}
    gateway4: {self._gw}
    nameservers:
      addresses: 
      - {self._ns}
      search: [covenant.mrmat.org, mrmat.org]
    routes:
      - to: 0.0.0.0/0
        via: {self._gw}
        metric: 1
        '''

    def __repr__(self):
        return f'NetworkConfig(mac={self._mac}, ip={self._ip}, gw={self._gw}, ns={self.ns}'
