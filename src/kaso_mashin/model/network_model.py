import enum
from kaso_mashin import Base
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column


class NetworkKind(enum.Enum):
    VMNET_HOST = 'host'
    VMNET_SHARED = 'shared'


class NetworkModel(Base):
    """
    Representation of a network in the database
    """
    __tablename__ = 'networks'
    network_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    kind: Mapped[NetworkKind] = mapped_column(Enum(NetworkKind))

    host_ip4: Mapped[str] = mapped_column(String(15))
    nm4: Mapped[str] = mapped_column(String(15))
    gw4: Mapped[str] = mapped_column(String(15))
    ns4: Mapped[str] = mapped_column(String(15))

    def __repr__(self) -> str:
        return f'NetworkModel(id={self.network_id!r}, ' \
               f'name={self.name!r}, ' \
               f'kind={self.kind!r}, ' \
               f'host_ip4={self.host_ip4!r}, ' \
               f'nm4={self.nm4}, ' \
               f'gw4={self.gw4!r}, ' \
               f'ns4={self.nm4!r}' \
               f')'
