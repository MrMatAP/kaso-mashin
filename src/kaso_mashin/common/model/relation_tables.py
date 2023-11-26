from sqlalchemy import Table, Column, ForeignKey

from kaso_mashin import Base

instance_to_identities = Table(
    'instance_identities',
    Base.metadata,
    Column('instance_id', ForeignKey('instances.instance_id')),
    Column('identity_id', ForeignKey('identities.identity_id'))
)
