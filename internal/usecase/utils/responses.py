from typing import Any, Dict, TypedDict

from fastapi import status
from fastapi.responses import Response
from typing_extensions import NotRequired


class ResponseExample(TypedDict):
    detail: NotRequired[str]


class ResponseSchema(dict):  # noqa: WPS600

    def __init__(
            self,
            status_code: int,
            description: str,
            example: ResponseExample,
    ) -> None:
        self.example = example
        self.status_code = status_code
        self.description = description
        super().__init__(self.schema(
            example=example,
            status_code=status_code,
            description=description,
        ))

    def __call__(self, detail: str = '', description: str = ''):
        example = self.example.copy()
        example['detail'] = detail or example['detail']
        return self.schema(
            example=example,
            status_code=self.status_code,
            description=description or self.description,
        )

    @classmethod
    def schema(
            cls,
            status_code: int,
            description: str,
            example: ResponseExample,
    ) -> Dict[int, Dict[str, Any]]:
        return {
            status_code: {
                'description': description,
                'content': {
                    'application/json': {
                        'data': example,
                    },
                },
            },
        }


class SuccessfulResponse(Response):

    def __init__(self, status_code: int = status.HTTP_204_NO_CONTENT):
        super().__init__(status_code=status_code)


HTTP_200_OK_REQUEST = ResponseSchema(
    status_code=status.HTTP_200_OK,
    description='OK',
    example=ResponseExample(detail='OK'),
)

HTTP_400_BAD_REQUEST = ResponseSchema(
    status_code=status.HTTP_400_BAD_REQUEST,
    description='Bad Request',
    example=ResponseExample(detail='Bad Request'),
)
HTTP_403_FORBIDDEN = ResponseSchema(
    status_code=status.HTTP_403_FORBIDDEN,
    description='Forbidden',
    example=ResponseExample(detail='Forbidden'),
)
HTTP_404_NOT_FOUND = ResponseSchema(
    status_code=status.HTTP_404_NOT_FOUND,
    description='Not Found',
    example=ResponseExample(detail='Not Found'),
)
