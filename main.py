import asyncio
from pydantic import SecretStr

from package.openai import PromptManager
from package.openai.client import ChatGPTClient
from internal.config import settings

# Пример использования:

manager_prompt = PromptManager()


async def main():
    # Замените 'your-api-key' на ваш реальный API ключ OpenAI
    api_key = SecretStr(settings.openai.token)
    system_prompt = manager_prompt.get_prompt('translate')

    client = ChatGPTClient(
        api_key,
        embeddings_model_name='text-embedding-ada-002',
        system_prompt=system_prompt,
    )

    # Создание эмбеддингов
    texts = [
        "Это пример текста для создания эмбеддингов.",
        "Еще один текст для эмбеддингов."
    ]
    embeddings = client.create_embeddings(texts)
    print("Эмбеддинги:", embeddings)

    # Токенизация текста
    text = "Это пример текста для токенизации."
    tokens = client.tokenize_text(text)
    print("Токены:", tokens)

    # Разбиение текста на части
    long_text = "Это очень длинный текст, который мы хотим разбить на части, чтобы не превышать лимит токенов одного запроса."
    chunks = client.split_text_into_chunks(long_text, chunk_size=client.max_tokens)
    print("Текст, разбитый на части:")
    for i, chunk in enumerate(chunks):
        print(f"Часть {i + 1}:", chunk)
        print("Количество токенов в части:", len(client.tokenize_text(chunk)))

    # Отправка сообщений в сессии чата
    messages = [
        "Здравствуйте, как у вас дела?",
        "Можете объяснить законы Ньютона?",
        "Какая столица Франции?"
    ]

    for message in messages:
        response = await client.send_message(message)
        print("Пользователь:", message)
        print("ChatGPT:", response)


if __name__ == "__main__":
    asyncio.run(main())
