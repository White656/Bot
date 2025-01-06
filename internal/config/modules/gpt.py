# Фабрика для MinioClient
from internal.config import settings
from package.openai import ChatGPTClient, PromptManager
from pydantic import SecretStr

manager_prompt = PromptManager()
system_prompt = manager_prompt.get_prompt('test')

api_key = SecretStr(settings.OPENAI_TOKEN)
client = ChatGPTClient(
    api_key,
    model_name='gpt-4o-mini',
    embeddings_model_name='text-embedding-ada-002',
    system_prompt=system_prompt,
)


def get_gpt_client() -> ChatGPTClient:
    return client
