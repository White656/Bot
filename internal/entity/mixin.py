import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin(object):

    created_at = sa.Column(
        psql.TIMESTAMP(timezone=True),
        default=sa.func.now(),
        server_default=sa.FetchedValue(),
    )
    updated_at = sa.Column(
        psql.TIMESTAMP(timezone=True),
        onupdate=sa.func.now(),
        server_default=sa.FetchedValue(),
        server_onupdate=sa.FetchedValue(),
    )
    deleted_at = sa.Column(
        psql.TIMESTAMP(timezone=True), server_default=sa.FetchedValue(),
    )
