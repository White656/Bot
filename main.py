import asyncio

from internal.config import settings
from internal.dto import OpenAIConversation

from package import pdf

from package.openai.client import ChatGptAPIClient

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
STEP = 10
OUTPUT_FILE = 'summary.txt'  # Имя файла для записи результата


def format_text(text: str) -> str:
    """
    Форматирует текст:
    - Заменяет `**` на жирный текст.
    - Добавляет отступы после каждого абзаца.
    """
    # Преобразование символов для форматирования
    formatted = text.replace('**', '**')  # Для жирного текста оставляем `**` как есть.

    # Разбиваем текст на абзацы и добавляем отступы
    paragraphs = formatted.split('\n')
    structured_text = '\n\n'.join(paragraph.strip() for paragraph in paragraphs).strip()
    return structured_text


async def main(content: str):
    client = ChatGptAPIClient(settings.openai)
    messages[1]['content'] = content
    requests = OpenAIConversation(
        model=settings.openai.model,
        max_tokens=settings.openai.max_tokens,
        messages=messages,
    )
    result = await client.completions(requests)
    return result['choices'][0]['message']['content']


with open('files/Инфаркт миокарда.pdf', 'rb') as pdf_file:
    processor = pdf.PDFProcessor(pdf_file)
    total_pages = processor.pages
    i = 0

    while i < total_pages:
        print(f"Processing pages {i} to {i + total_pages - 1}")
        texts = ''

        # Обрабатываем страницы
        processor.process_pdf(start_page=i, end_page=min(i + STEP, total_pages))
        for item in processor.extract():
            texts += f'{item}\n'

        # Генерация резюме
        raw_summary = asyncio.run(main(content=texts))

        # Форматирование текста
        formatted_summary = format_text(raw_summary)

        # Добавляем текст с разметкой
        content += f'\n--- Страницы {i + 1} - {min(i + STEP, total_pages)} ---\n\n{formatted_summary}\n\n'

        i += STEP

# Запись результата в файл
with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
    file.write(content)

print(f"Summary saved to {OUTPUT_FILE}")