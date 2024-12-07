from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Coroutine, Generic, TypeVar

from fastapi import Query
from pydantic.generics import GenericModel

T = TypeVar('T')


@dataclass
class Params(object):  # noqa: WPS110

    page: int = Query(1, ge=1, description='Page number')
    size: int = Query(50, ge=1, le=500, description='Page size')

    @property
    def limit(self) -> int:
        return self.size

    @property
    def offset(self) -> int:
        return self.size * (self.page - 1)


class Page(GenericModel, Generic[T]):
    items: list[T]  # noqa: WPS110

    total: int
    page: int
    size: int


PaginationEndpoint = Callable[[...], Coroutine[Any, Any, tuple[list[T], int]]]
PaginationWrapper = Callable[[...], Coroutine[Any, Any, Page[T]]]


def paginate(func: PaginationEndpoint) -> PaginationWrapper:
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Page[T]:
        dto = kwargs.get('dto')
        items, total = await func(*args, **kwargs)  # noqa: WPS110
        return Page[T](items=items, total=total, page=dto.page, size=dto.size)

    return wrapper
