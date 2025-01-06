from fastapi import FastAPI, HTTPException
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

    app.include_router(api_router, prefix=settings.API)
    app.dependency_overrides.setdefault(*database.override_session)

    app.add_exception_handler(DBAPIError, database_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(NoResultFound, database_not_found_handler)

    return app
