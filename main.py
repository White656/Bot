import asyncio
import ssl
import certifi

from internal.config import settings
from internal.dto import OpenAIConversation

from package.openai.client import ChatGptAPIClient
from package.pdf.main import PDFProcessor  # Ваш PDFProcessor

messages = [
    {"role": "system",
     "content": """
     Ты — ассистент, который составляет краткий пересказ полученного текста.
      Необходимо оставлять основную мысль, терминологию.
       Изложи все понятным языком. Объем должен сократиться примерно в 2 раза от первоначального.
       """},
    {"role": "user", "content": "text"}
]

content = ''
STEP = 7
OUTPUT_FILE = 'summary.txt'


async def main(content: str):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    client = ChatGptAPIClient(settings.openai, ssl_context=ssl_context)

    messages[1]['content'] = content
    requests = OpenAIConversation(
        model=settings.openai.model,
        max_tokens=settings.openai.max_tokens,
        messages=messages,
    )
    result = await client.completions(requests)
    return result['choices'][0]['message']['content']


with open('files/Хобл.pdf', 'rb') as pdf_file:
    processor = PDFProcessor(pdf_file)
    total_pages = processor.pages
    i = 0

    while i < total_pages:
        # Ограничение для диапазона страниц
        start_page = i
        end_page = max(i + STEP, total_pages)

        print(f"Processing pages {start_page + 1} to {end_page}")

        # Обработка страниц
        processor.process_pdf(start_page=start_page, end_page=end_page)
        extracted_texts = '\n'.join(processor.extract())  # Извлекаем текст из диапазона

        if not extracted_texts.strip():
            print(f"No text extracted from pages {start_page + 1} to {end_page}")
        else:
            # Генерация резюме через OpenAI API
            raw_summary = asyncio.run(main(content=extracted_texts))

            # Добавляем текст с разметкой
            content += f'\n--- Страницы {start_page + 1} - {end_page} ---\n\n{raw_summary}\n\n'

        # Увеличиваем шаг
        i += STEP

# Запись результата в файл
with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
    file.write(content)

print(f"Summary saved to {OUTPUT_FILE}")
