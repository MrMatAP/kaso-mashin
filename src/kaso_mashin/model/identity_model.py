import enum

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import Base


class IdentityKind(enum.Enum):
    PUBKEY = 'pubkey'
    PASSWORD = 'password'


class IdentityModel(Base):
    """
    Representation of an identity in the database
    """

    __tablename__ = 'identities'
    identity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[IdentityKind] = mapped_column(Enum(IdentityKind))

    credentials: Mapped[str] = mapped_column(String)

    def __repr__(self) -> str:
        return f'IdentityModel(identity_id={self.identity_id}, ' \
               f'name="{self.name}", ' \
               f'kind="{self.kind}", ' \
               f'credentials=**MASKED**)'
