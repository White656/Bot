from fastapi import HTTPException, status


class HTTPException(HTTPException):  # noqa: WPS440

    def __call__(self, detail: str) -> HTTPException:
        return HTTPException(self.status_code, detail)


HTTP_400_BAD_REQUEST = HTTPException(
    detail='Bad Request',
    status_code=status.HTTP_400_BAD_REQUEST,
)
HTTP_401_UNAUTHORIZED = HTTPException(
    detail='Unauthorized',
    status_code=status.HTTP_401_UNAUTHORIZED,
)
HTTP_403_FORBIDDEN = HTTPException(
    detail='Forbidden',
    status_code=status.HTTP_403_FORBIDDEN,
)
HTTP_404_NOT_FOUND = HTTPException(
    detail='Not Found',
    status_code=status.HTTP_404_NOT_FOUND,
)
