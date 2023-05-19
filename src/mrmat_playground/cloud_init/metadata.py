

class Metadata:
    """
    Manages and renders cloud-init Metadata
    """

    def __init__(self, instance_id: str, hostname: str):
        self._instance_id = instance_id
        self._hostname = hostname

    def render(self) -> str:
        return f'''
instance-id: {self._instance_id}/{self._hostname}
local-hostname: {self._hostname}
        '''

    def __repr__(self):
        return f'Metadata(instance_id={self._instance_id}, hostname={self._hostname})'
