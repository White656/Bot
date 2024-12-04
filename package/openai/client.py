from typing import List, Any, Optional
from pydantic import SecretStr
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import tiktoken
from sqlalchemy.orm.instrumentation import manager_of_class
from package.openai import PromptManager



class ChatGPTClient:
    def __init__(
            self,
            api_key: SecretStr,
            model_name: str = 'gpt-4',
            embeddings_model_name: str = 'text-embedding-ada-002',
            system_prompt: Optional[str] = None,
    ):
        self._api_key = api_key
        self.model_name = model_name
        self.embeddings_model_name = embeddings_model_name
        self.chat_model = ChatOpenAI(
            openai_api_key=self._api_key,
            model_name=self.model_name
        )
        self.embeddings_model = OpenAIEmbeddings(
            openai_api_key=self._api_key,
            model=self.embeddings_model_name
        )
        self.chat_history = []

        # Явно указываем токенизаторы
        self.tokenizer = tiktoken.get_encoding('cl100k_base')
        self.embeddings_tokenizer = tiktoken.get_encoding('cl100k_base')

        # Установка системного промпта, если он предоставлен
        self.system_prompt = system_prompt
        if self.system_prompt:
            system_message = SystemMessage(content=self.system_prompt)
            self.chat_history.append(system_message)

        # Установка лимитов токенов в зависимости от моделей
        self.max_tokens = self.get_model_token_limit(self.model_name)
        self.embeddings_max_tokens = self.get_model_token_limit(self.embeddings_model_name)

    def get_model_token_limit(self, model_name: str) -> int:
        # Определение лимитов токенов для различных моделей
        model_token_limits = {
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'text-embedding-ada-002': 8191  # Лимит для модели эмбеддингов
        }
        return model_token_limits.get(model_name, 4096)  # По умолчанию 4096, если модель не найдена

    def create_embeddings(self, texts: List[str]) -> List[Any]:
        # Убедимся, что каждый текст не превышает лимит токенов для эмбеддинговой модели
        valid_texts = []
        for text in texts:
            tokens = self.embeddings_tokenizer.encode(text)
            if len(tokens) <= self.embeddings_max_tokens:
                valid_texts.append(text)
            else:
                # Разбиваем текст на части
                chunks = self.split_text_into_chunks(
                    text,
                    self.embeddings_max_tokens,
                    tokenizer=self.embeddings_tokenizer
                )
                valid_texts.extend(chunks)
        return self.embeddings_model.embed_documents(valid_texts)

    def tokenize_text(self, text: str, tokenizer=None) -> List[int]:
        if tokenizer is None:
            tokenizer = self.tokenizer
        tokens = tokenizer.encode(text)
        return tokens

    def split_text_into_chunks(self, text: str, chunk_size: int, tokenizer=None) -> List[str]:
        if tokenizer is None:
            tokenizer = self.tokenizer
        tokens = self.tokenize_text(text, tokenizer)
        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
        return chunks

    async def send_message(self, message: str) -> str:
        # Проверяем, не превышает ли сообщение лимит токенов модели
        message_tokens = self.tokenize_text(message)
        # Считаем общее количество токенов в истории чата
        total_tokens = sum(len(self.tokenize_text(msg.content)) for msg in self.chat_history) + len(message_tokens)

        if total_tokens > self.max_tokens:
            # Обрезаем историю чата, чтобы не превышать лимит
            self.trim_chat_history(len(message_tokens))

        human_message = HumanMessage(content=message)
        self.chat_history.append(human_message)
        assistant_message = await self.chat_model.ainvoke(self.chat_history)
        self.chat_history.append(assistant_message)
        return assistant_message.content

    def trim_chat_history(self, new_message_tokens_length):
        # Оставляем только последние сообщения, чтобы общее количество токенов не превышало лимит
        total_tokens = new_message_tokens_length
        trimmed_history = []
        # Начинаем с последних сообщений
        for message in reversed(self.chat_history):
            message_tokens = len(self.tokenize_text(message.content))
            if (total_tokens + message_tokens) <= self.max_tokens:
                trimmed_history.insert(0, message)  # Вставляем в начало
                total_tokens += message_tokens
            else:
                break
        self.chat_history = trimmed_history

    def reset_chat_history(self):
        self.chat_history = []
        # Повторно добавляем системный промпт, если он есть
        if self.system_prompt:
            system_message = SystemMessage(content=self.system_prompt)
            self.chat_history.append(system_message)
