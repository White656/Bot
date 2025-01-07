from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DBAPIError, NoResultFound

from internal.config import settings
from internal.config.modules import database
from internal.controller.http.router import api_router
from internal.usecase.utils import (
    database_error_handler,
    database_not_found_handler,
    http_exception_handler,
)
from internal.usecase.utils.responses import DynamicResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url='{0}/openapi.json'.format(settings.DOCS),
        swagger_ui_parameters=settings.SWAGGER_UI_PARAMETERS,
    )

    if settings.APP_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin)
                for origin in settings.APP_CORS_ORIGINS
            ],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    @app.middleware("http")
    async def check_header(request: Request, call_next):
        """
        Function to create and configure a FastAPI application instance.

        This function sets up the FastAPI application and adds necessary configurations, such as the
        middleware used for validating specific HTTP headers. The middleware checks for the existence
        and correctness of a required header key and value in all incoming requests. If the header is
        missing or invalid, the request is rejected with a 403 status code and an appropriate error
        message is returned.

        Returns:
            An instance of the FastAPI application with the defined middleware applied.

        Raises:
            HTTPException: When the required header key is not present or contains an invalid value.
        """
        if settings.DEBUG:
            return await call_next(request)
        required_header_key = "X-Admin-Header"
        required_header_value = settings.ADMIN_KEY

        if request.headers.get(required_header_key) != required_header_value:
            return DynamicResponse.create(
                status_code=403,
                description='Invalid or missing header',
                detail='Forbidden',
            )

        response = await call_next(request)
        return response

    app.include_router(api_router, prefix=settings.API)
    app.dependency_overrides.setdefault(*database.override_session)

    app.add_exception_handler(DBAPIError, database_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(NoResultFound, database_not_found_handler)

    return app
