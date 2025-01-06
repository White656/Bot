from contextlib import asynccontextmanager

from internal.config.modules.database import get_database_client


@asynccontextmanager
async def get_service(service_class):
    """
    An asynchronous context manager for obtaining and managing a service instance.

    This function is designed to provide a service instance of the specified
    service class, utilizing a session created by the asynchronous database client.
    It ensures proper cleanup of the session once the context is exited. This
    function supports dependency injection by creating the service with the session
    as its initialization parameter.

    Args:
        service_class: The class of the service to be managed. This should be a
        subclass of `Service`.

    Yields:
        An instance of the provided `service_class`, initialized with the session.

    Raises:
        Any exceptions raised within the context will propagate back to the caller.
    """
    async for session in get_database_client():
        service = service_class(session)
        try:
            yield service
        finally:
            await session.close()
