import typing


class ScriptComponent:
    """
    An interface class for the vm_script model to retrieve parameters
    """

    def parameters(self) -> typing.List[str]:
        return []
