from ssl import SSLContext
from typing import Any, AsyncIterator, Awaitable, Callable, Literal, Coroutine, Protocol

from aiohttp.client import ClientResponse, ClientSession
from package.openai.exceptions import OpenAIRequestError

from internal.config import settings
from internal.dto import OpenAIConversation, OpenAIEmbeddings


class OpenAIConfig(Protocol):
    url: str
    token: str
    model: str
    temperature: float
    max_tokens: int


class ChatGptAPIClient(object):

    def __init__(self, config: OpenAIConfig, ssl_context: SSLContext = None):
        self._config = config
        self.headers = {
            'Authorization': f'Bearer {self._config.token}',
            'Content-Type': 'application/json',
        }
        self.api_url = config.url
        self.ssl_context = ssl_context

    async def completions(self, request: OpenAIConversation) -> Coroutine[Any, Any, Any]:
        return await self._make_request(
            method='post',
            url=self._make_endpoint_url('/chat/completions'),
            serializer=self._json,
            json=request.dict(),
        )

    async def embeddings(self, request: OpenAIEmbeddings):
        ...

    async def models(self) -> Coroutine[Any, Any, Any]:
        return await self._make_request(
            method='get',
            url=self._make_endpoint_url('/models'),
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
        async with ClientSession(headers=self.headers) as session:
            async with getattr(session, method)(url, json=json, params=query, ssl=self.ssl_context) as response:
                if not response.ok:
                    response_data: dict[str, Any] = await response.json()
                    raise OpenAIRequestError(
                        error=response_data['error'],
                        detail=response_data['error']['message'],
                    )

                return await serializer(response)

    def _make_endpoint_url(self, method: str) -> str:
        return self._config.url + method

    async def _json(self, response: ClientResponse) -> Any:
        return await response.json()

    async def _bytes(self, response: ClientResponse) -> bytes:
        return await response.read()
