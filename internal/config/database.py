from typing import Any, AsyncContextManager, AsyncGenerator, Callable

from sqlalchemy import orm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from internal.config import settings
from internal.usecase.utils import get_session

AsyncSessionGenerator = AsyncGenerator[AsyncSession, None]


def async_session(
        url: str, *, wrap: Callable[..., Any] | None = None,  # noqa: WPS318
) -> Callable[..., AsyncSessionGenerator] | AsyncContextManager[Any]:
    engine = create_async_engine(
        url, pool_pre_ping=True, future=True,
    )
    factory = orm.sessionmaker(
        engine, class_=AsyncSession, autoflush=False, expire_on_commit=False,
    )

    async def get_session() -> AsyncSessionGenerator:  # noqa: WPS430, WPS442
        async with factory() as session:
            yield session

    return get_session if wrap is None else wrap(get_session)


override_session = get_session, async_session(settings.migrations_url)
