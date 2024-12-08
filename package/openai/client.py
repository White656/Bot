import logging
from typing import Any, List, Optional

import tiktoken
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import SecretStr


class ChatGPTClient(object):
    def __init__(
            self,
            api_key: SecretStr,
            model_name: str = 'gpt-4o-mini',
            embeddings_model_name: str = 'text-embedding-ada-002',
            system_prompt: Optional[str] = None,
            mathematical_percent: Optional[int] = 20,
    ):
        """Initializes the configuration for interacting with OpenAI's GPT-4 and text
        embedding models.It sets up the necessary components to communicate with the
        OpenAI API, including chat and embeddings model instances, tokenizers, and the
        system prompt if provided. The class handles token limit settings based on the
        specified models and manages initial chat history.

        Args:
            api_key: A secret string representing the OpenAI API key required for
                authentication.
            model_name: The name of the chat model to be used, defaulting to 'gpt-4'.
                Determines which model to use for chat operations.
            embeddings_model_name: The name of the embeddings model to be used,
                defaulting to 'text-embedding-ada-002'. It defines which model is to be
                utilized for handling text embeddings.
            system_prompt: An optional string for setting a system-level prompt
                message. If provided, it initializes the conversation context with this
                prompt.
            mathematical_p: An optional integer defining a mathematical parameter,
                defaulting to 100. This parameter may be used for internal calculations
                or configurations.

        """
        self._api_key = api_key
        self.model_name = model_name
        self.math_p = mathematical_percent
        self.embeddings_model_name = embeddings_model_name
        self.chat_model = ChatOpenAI(
            openai_api_key=self._api_key,
            model_name=self.model_name,
        )
        self.embeddings_model = OpenAIEmbeddings(
            openai_api_key=self._api_key,
            model=self.embeddings_model_name,
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

        self.token = self.get_model_token_limit(self.model_name)
        self.max_tokens = self.token - int((self.token / 100) * self.math_p)
        self.embeddings_max_tokens = self.get_model_token_limit(self.embeddings_model_name)

    def get_model_token_limit(self, model_name: str) -> int:
        """Retrieves the token limit for a specified model.

        This function takes a model name as input and returns the token limit
        associated with that model. It uses a predefined dictionary to map
        model names to their respective token limits. If the provided model
        name is not found in the dictionary, a default token limit is
        returned.

        Args:
            model_name: The name of the model for which the token limit is
                requested.

        Returns:
            The token limit for the specified model. If the model is not
            found, a default value of 4096 is returned.
        """
        model_token_limits = {
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'gpt-4': 8192,
            # 'gpt-4o-mini': 16384,
            'gpt-4o-mini': 1900,  # специально для точного пересказа текстов.
            'gpt-4-32k': 32768,
            'text-embedding-ada-002': 8191,  # Лимит для модели эмбеддингов
        }
        return model_token_limits.get(model_name, 2000)  # По умолчанию 4096, если модель не найдена

    def create_embeddings(self, texts: List[str]) -> List[Any]:
        """Creates embeddings for the provided texts.

        This method processes a list of texts by tokenizing each text and checking
        if the number of tokens is within the specified maximum tokens limit. If a
        text exceeds the token limit, it splits the text into smaller chunks that
        fit the limit. It then generates embeddings for all valid texts or chunks
        using the specified embeddings model.

        Args:
            texts (List[str]): A list of input texts to generate embeddings for.

        Returns:
            List[Any]: A list containing the embeddings of the valid texts.
        """
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
                    tokenizer=self.embeddings_tokenizer,
                )
                valid_texts.extend(chunks)
        logging.info('Create Embeddings.')
        return self.embeddings_model.embed_documents(valid_texts)

    def tokenize_text(self, text: str, tokenizer=None) -> List[int]:
        """Tokenizes the input text using the specified tokenizer. If no
        tokenizer is provided, the default one is used. The function
        returns a list of token IDs that represent the text in a format
        suitable for processing by language models.

        Args:
            text (str): The text to be tokenized.
            tokenizer: The tokenizer instance to use for tokenization. If
                None, the default tokenizer of the class is used.

        Returns:
            List[int]: A list of integer token IDs representing the
            tokenized form of the input text.
        """
        if tokenizer is None:
            tokenizer = self.tokenizer
        tokens = tokenizer.encode(text)
        logging.info('Tokenize text.')
        return tokens

    def split_text_into_chunks(self, text: str, chunk_size: int, tokenizer=None) -> List[str]:  # noqa: WPS210
        """Splits the provided text into chunks based on a specified chunk size. The text is
        tokenized using the provided tokenizer (or a default tokenizer), divided into segments
        of tokens, and then each segment is decoded back into a text chunk. This function is
        useful for handling large text by processing it in smaller manageable pieces.

        Args:
            text: The input text that needs to be chunked.
            chunk_size: The number of tokens each chunk should contain.
            tokenizer: An optional tokenizer to be used for tokenizing the text. If no tokenizer
                       is provided, a default tokenizer is used.

        Returns:
            A list of strings where each string is a chunk of the original text.
        """
        if tokenizer is None:
            tokenizer = self.tokenizer
        tokens = self.tokenize_text(text, tokenizer)
        chunks = []
        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
        logging.info('Split text to chunks.')
        return chunks

    async def send_message(self, message: str) -> str:
        """Sends a message to a chat model and receives a response. This function
        manages chat history by appending the human message and assistant
        response, and ensures that the token limit for the model is not
        exceeded before sending the message.

        Args:
            message (str): The message content to be sent to the chat model.

        Returns:
            str: The response content from the chat model.
        """
        # Проверяем, не превышает ли сообщение лимит токенов модели
        human_message = HumanMessage(content=message)
        new_message_tokens = len(self.tokenize_text(human_message.content))
        self.trim_chat_history(new_message_tokens)
        self.chat_history.append(human_message)
        assistant_message = await self.chat_model.ainvoke(self.chat_history)
        self.chat_history.append(assistant_message)
        logging.info('Send message to OpenAI client.')
        return assistant_message.content

    def trim_chat_history(self, new_message_tokens_length):
        """Trims the chat history to ensure the total number of tokens does not exceed
        a predefined maximum. This function iterates through the chat history
        starting from the most recent message, adding messages to a trimmed history
        list until the token limit is reached.

        Args:
            new_message_tokens_length: The number of tokens in the new message
                to be considered alongside the existing chat history.
        """

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
        """Manages the chat history including adding system prompts when necessary.

        Attributes:
            chat_history (list): A list that stores the chat history.
            system_prompt (str): A string representing the system prompt to be added
                to chat history, if it exists.
        """
        self.chat_history = []
        # Повторно добавляем системный промпт, если он есть
        if self.system_prompt:
            system_message = SystemMessage(content=self.system_prompt)
            self.chat_history.append(system_message)
        logging.info('Reset chat history.')
