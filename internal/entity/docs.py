import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

from internal.entity.base import Base
from internal.entity.mixin import TimestampMixin
from sqlalchemy.orm import relationship


class Docs(TimestampMixin, Base):
    name = sa.Column(sa.String(255), nullable=True)
    checksum = sa.Column(sa.BigInteger, nullable=True)
    s3_briefly = sa.Column(sa.String(255), nullable=True)
    milvus_docs = relationship('MilvusDocs', back_populates='docs', uselist=True)


class MilvusDocs(TimestampMixin, Base):
    id = ...
    milvus_id = sa.Column(sa.Integer, primary_key=True)
    docs_id = sa.Column(psql.UUID(as_uuid=True), sa.ForeignKey('docs.id'), primary_key=True, nullable=False)
    docs = relationship('Docs', back_populates='milvus_docs')
