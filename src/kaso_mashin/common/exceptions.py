class KasoMashinException(Exception):
    """
    A dedicated exception for mrmat-playground
    """

    def __init__(self, status: int = 500, msg: str = "An unknown exception occurred", task = None):
        super().__init__(msg)
        self._status = status
        self._msg = msg
        if task:
            self._task = task
            self._task.state = "failed"
            self._task.msg = msg

    @property
    def kind(self) -> str:
        return self.__class__.__name__

    @property
    def status(self) -> int:
        return self._status

    @property
    def msg(self) -> str:
        return self._msg

    @property
    def task(self):
        return self._task

    def __str__(self) -> str:
        return f"[{self._status}] {self._msg}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self._status}, msg={self._msg})"


class BootstrapException(KasoMashinException):
    """
    Exception for bootstrap-related issues
    """
    pass


class DiskException(KasoMashinException):
    """
    Exception for disk-related issues
    """
    pass


class IdentityException(KasoMashinException):
    """
    Exception for identity-related issues
    """
    pass


class ImageException(KasoMashinException):
    """
    Exception for image-related issues
    """
    pass


class InstanceException(KasoMashinException):
    """
    Exception for instance-related issues
    """
    pass


class NetworkException(KasoMashinException):
    """
    Exception for network-related issues
    """
    pass


class EntityNotFoundException(KasoMashinException):
    """
    Exception raised when no entity can be found
    """

    def __init__(self, status: int = 404, msg: str = "No such entity could be found", task=None):
        super().__init__(status, msg, task)


class EntityInvariantException(KasoMashinException):
    """
    Exception raised when there is something wrong with the entity
    """
    pass
