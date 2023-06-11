from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kaso_mashin import Base


class IdentityModel(Base):
    """
    Representation of an identity in the database
    """

    __tablename__ = 'identities'
    identity_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    public_key: Mapped[str] = mapped_column(String)
