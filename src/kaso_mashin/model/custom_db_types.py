import pathlib
import ipaddress
import typing

import sqlalchemy.types
from sqlalchemy import Dialect
from sqlalchemy.sql.type_api import _T


class IP4Address(sqlalchemy.types.TypeDecorator):
    """
    Marshals/Unmarshals IP addresses from a string in the database
    """

    impl = sqlalchemy.types.Unicode
    cache_ok = True

    def process_bind_param(self, value: typing.Optional[_T], dialect: Dialect) -> typing.Any:
        return str(value) if value else None

    def process_result_value(self, value: typing.Optional[str], dialect: Dialect) -> ipaddress.IPv4Address | None:
        return ipaddress.ip_address(value) if value else None


class DbPath(sqlalchemy.types.TypeDecorator):
    """
    Marshals/Unmarshals a pathlib.Path from a string in the database
    """

    impl = sqlalchemy.types.Unicode
    cache_ok = True

    def process_bind_param(self, value: pathlib.Path, dialect: Dialect) -> str:
        """
        Parse pathlib.Path into its string representation
        Args:
            value: The pathlib.Path
            dialect: Ignored

        Returns:
            A unicode string
        """
        return str(value)

    def process_result_value(self, value: typing.Optional[str], dialect: Dialect) -> pathlib.Path | None:
        """
        Parse the string from the database into pathlib.Path
        Args:
            value: The string in the database column
            dialect: Ignored

        Returns:
            An initialised pathlib.Path
        """
        return pathlib.Path(value) if value else None
