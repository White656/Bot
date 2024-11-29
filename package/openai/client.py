from typing import Any, Awaitable, Callable, Coroutine, Literal, Protocol
from aiohttp.client import ClientResponse, ClientSession
from aiohttp import ClientTimeout
from package.openai.exceptions import OpenAIRequestError
from internal.dto import OpenAIConversation, OpenAIEmbeddings


class OpenAIConfig(Protocol):
    """Configuration interface for OpenAI API."""
    url: str
    token: str
    model: str
    temperature: float
    max_tokens: int


class ChatGptAPIClient:
    """
    Client for interacting with the OpenAI API.

    Provides methods to access OpenAI endpoints for chat completions, embeddings, and models.
    Supports extensibility and reusable HTTP request handling.

    Attributes:
        _config (OpenAIConfig): The configuration for API access.
        headers (dict): Default headers for API requests.
        api_url (str): Base URL of the OpenAI API.
        timeout (ClientTimeout): Timeout settings for API requests.
    """

    ENDPOINTS = {
        'chat_completions': '/chat/completions',
        'embeddings': '/embeddings',
        'models': '/models',
    }

    def __init__(self, config: OpenAIConfig, timeout: float = 30.0, extra_headers: dict[str, str] | None = None):
        """
        Initializes the ChatGptAPIClient.

        Args:
            config (OpenAIConfig): The configuration object for OpenAI API access.
            timeout (float): Timeout in seconds for API requests. Defaults to 30 seconds.
            extra_headers (dict[str, str] | None): Additional headers to include in requests.
        """
        self._config = config
        self.headers = {
            'Authorization': f'Bearer {self._config.token}',
            'Content-Type': 'application/json',
        }
        if extra_headers:
            self.headers.update(extra_headers)
        self.api_url = config.url
        self.timeout = ClientTimeout(total=timeout)

    async def completions(self, request: OpenAIConversation) -> Coroutine[Any, Any, Any]:
        """
        Calls the OpenAI API for chat completions.

        Args:
            request (OpenAIConversation): Request object with conversation details.

        Returns:
            Coroutine[Any, Any, Any]: Response from the OpenAI API.
        """
        return await self._make_request(
            method='post',
            url=self._make_endpoint_url(self.ENDPOINTS['chat_completions']),
            serializer=self._json,
            json=request.dict(),
        )

    async def embeddings(self, request: OpenAIEmbeddings) -> Coroutine[Any, Any, Any]:
        """
        Calls the OpenAI API to generate embeddings for the given input.

        Args:
            request (OpenAIEmbeddings): Request object containing input text and model parameters.

        Returns:
            Coroutine[Any, Any, Any]: Embeddings response from the OpenAI API.
        """
        return await self._make_request(
            method='post',
            url=self._make_endpoint_url(self.ENDPOINTS['embeddings']),
            serializer=self._json,
            json=request.dict(),
        )

    async def models(self) -> Coroutine[Any, Any, Any]:
        """
        Fetches available models from the OpenAI API.

        Returns:
            Coroutine[Any, Any, Any]: List of models supported by the OpenAI API.
        """
        return await self._make_request(
            method='get',
            url=self._make_endpoint_url(self.ENDPOINTS['models']),
            serializer=self._json,
        )

    async def _make_request(
            self,
            method: Literal['get', 'post', 'put', 'patch', 'delete'],
            url: str,
            serializer: Callable[[ClientResponse], Awaitable[Any]],
            *,
            json: dict[str, Any] | None = None,
            query: dict[str, Any] | None = None,
    ) -> Any:
        """
        Handles HTTP requests to the OpenAI API.

        Args:
            method (Literal['get', 'post', 'put', 'patch', 'delete']): HTTP method.
            url (str): Target URL for the API request.
            serializer (Callable[[ClientResponse], Awaitable[Any]]): Function to process the response.
            json (dict[str, Any] | None): JSON payload for the request. Defaults to None.
            query (dict[str, Any] | None): Query parameters for the request. Defaults to None.

        Returns:
            Any: Deserialized response data.

        Raises:
            OpenAIRequestError: If the response status is not OK.
        """
        async with ClientSession(headers=self.headers, timeout=self.timeout) as session:
            async with getattr(session, method)(url, json=json, params=query) as response:
                if not response.ok:
                    response_data: dict[str, Any] = await response.json()
                    raise OpenAIRequestError(
                        error=response_data.get('error'),
                        detail=response_data.get('error', {}).get('message', 'Unknown error'),
                    )
                return await serializer(response)

    def _make_endpoint_url(self, endpoint: str) -> str:
        """
        Constructs the full URL for a given endpoint.

        Args:
            endpoint (str): Endpoint path.

        Returns:
            str: Full API URL.
        """
        return self.api_url.rstrip('/') + endpoint

    async def _json(self, response: ClientResponse) -> Any:
        """
        Parses a JSON response.

        Args:
            response (ClientResponse): HTTP response object.

        Returns:
            Any: Parsed JSON data.
        """
        return await response.json()

    async def _bytes(self, response: ClientResponse) -> bytes:
        """
        Reads a binary response.

        Args:
            response (ClientResponse): HTTP response object.

        Returns:
            bytes: Raw response content.
        """
        return await response.read()
