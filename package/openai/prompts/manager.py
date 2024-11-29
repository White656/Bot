class PromptManager:
    """
    Класс для управления промтами, используемыми для взаимодействия с OpenAI API.
    """

    def __init__(self):
        self.prompts = {
            "summary": """
                Ты — ассистент, который составляет краткий пересказ полученного текста.
                Необходимо оставлять основную мысль, терминологию.
                Изложи все понятным языком. Объем должен сократиться примерно в 2 раза от первоначального.
            """,
            "translate": """
                Ты — переводчик. Переведи текст на русский язык. Используй естественный, литературный язык.
            """,
            "keywords": """
                Ты — аналитик. Найди ключевые слова и фразы из текста. Укажи их в списке, сохраняя контекст.
            """
        }

    def get_prompt(self, key: str) -> str:
        """
        Возвращает текст промта по ключу.

        Args:
            key (str): Ключ промта.

        Returns:
            str: Текст промта.

        Raises:
            KeyError: Если ключ отсутствует в списке промтов.
        """
        if key not in self.prompts:
            raise KeyError(f"Prompt with key '{key}' not found.")
        return self.prompts[key]

    def add_prompt(self, key: str, prompt: str):
        """
        Добавляет новый промт.

        Args:
            key (str): Ключ для нового промта.
            prompt (str): Текст промта.
        """
        self.prompts[key] = prompt
