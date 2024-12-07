from typing import Generic, TypeVar, get_args
from uuid import UUID

import sqlalchemy as sa
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from internal.entity.base import Base
from internal.usecase.utils import exceptions, get_session
from package.pagination import Params

T = TypeVar('T')


class Service(Generic[T]):  # noqa: WPS214, WPS338

    model: Base

    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    def __init_subclass__(cls):
        cls.model = get_args(cls.__orig_bases__[0])[0]

    def raise_not_found(self) -> None:
        raise exceptions.HTTP_404_NOT_FOUND(
            'Not found {0}'.format(self.model.__name__),
        )

    async def get_one(self, id: UUID, *where, **filter_by) -> T:
        instance = await self.get_one_or_none(id, *where, **filter_by)
        if instance is None:
            self.raise_not_found()

        return instance

    async def get_one_or_none(self, id: UUID, *where, **filter_by) -> T | None:
        return await self.session.scalar(
            sa.select(self.model).filter_by(
                id=id, deleted_at=None, **filter_by,
            ).where(*where),
        )

    async def select(self, dto: Params, *where, **filter_by) -> tuple[list[T], int]:
        instance_set = await self.session.scalars(
            sa.select(self.model).where(*where).filter_by(
                deleted_at=None, **filter_by,
            ).limit(dto.limit).offset(dto.offset),
        )
        return instance_set.unique().all(), await self.count(*where)

    async def select_all(self, *where, **filter_by) -> list[T]:
        instance_set = await self.session.scalars(
            sa.select(self.model).filter_by(deleted_at=None, **filter_by).where(*where),
        )
        return instance_set.unique().all()

    async def create(self, dto: BaseModel) -> T:
        instance = self.model(**dto.dict())
        self.session.add(instance)
        await self.session.commit()

        return instance

    async def create_many(self, dto_set: list[BaseModel]) -> list[T]:
        instance_set = [self.model(**dto.dict()) for dto in dto_set]
        self.session.add_all(instance_set)
        await self.session.commit()

        return instance_set

    async def update(self, id: UUID, **values) -> T:
        await self.session.execute(
            sa.update(self.model).filter_by(id=id).values(**values),
        )
        await self.session.commit()

        return await self.get_one(id)

    async def delete(self, id: UUID) -> None:
        await self.get_one(id)

        await self.session.execute(
            sa.update(self.model).filter_by(id=id).values(deleted_at=sa.func.now()),
        )
        await self.session.commit()

    async def count(self, *where, **filter_by) -> int:
        return await self.session.scalar(
            sa.select(sa.func.count(self.model.id)).filter_by(
                **filter_by, deleted_at=None,
            ).where(*where),
        )
