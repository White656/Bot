from typing import Any, Dict, TypedDict

from fastapi import status
from fastapi.responses import Response
from typing_extensions import NotRequired

from fastapi.responses import JSONResponse


class DynamicResponse:

    @staticmethod
    def schema(status_code: int, description: str, example: dict) -> dict:
        """
        This static method generates a structured dictionary schema for an HTTP response, which includes the status code,
        description of the response, and an example payload. It organizes the data in a manner consistent with common API
        documentation formats.

        Arguments:
            status_code (int): The HTTP status code to be included in the response schema.
            description (str): A textual description associated with the provided status code.
            example (dict): A sample JSON payload illustrating the response structure and data.

        Returns:
            dict: A dictionary structure representing the HTTP response schema, formatted for API documentation purposes.
        """
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

    @staticmethod
    def create(
            status_code: int,
            detail: str,
            description: str = '',
            example: dict = None,
    ) -> JSONResponse:
        """
            Creates a JSONResponse object configured with a specific status code,
            description, detail message, and optional example content. This method
            provides a structured response format for JSON-based API responses.

            Parameters:
            status_code: int
                The HTTP status code to include in the response.
            description: str
                A brief description of the response.
            detail: str
                A detailed message or additional information to include in the response content.
            example: dict, optional
                Example data to include in the response. If not provided, a default
                dictionary with only the detail message will be used.

            Returns:
            JSONResponse
                A JSONResponse object containing the provided status code, description,
                and structured content with the example data.
        """
        if example is None:
            example = {}

        # Наполняем пример данными
        example['detail'] = detail

        # Возвращяем JSONResponse в требуемом формате
        return JSONResponse(
            status_code=status_code,
            content={
                "status_code": status_code,
                "description": description,
                "content": {
                    "application/json": {
                        "data": example,
                    },
                },
            },
        )


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
