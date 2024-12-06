import asyncio

from pydantic import SecretStr
from pydantic import SecretStr

from package.openai import PromptManager
from package.openai.client import ChatGPTClient
from internal.config import settings
from package.pdf import PDFProcessor

# Пример использования:

manager_prompt = PromptManager()


async def main():
    api_key = SecretStr(settings.openai.token)
    system_prompt = manager_prompt.get_prompt('summary')

    client = ChatGPTClient(
        api_key,
        model_name='gpt-4o-mini',
        embeddings_model_name='text-embedding-ada-002',
        system_prompt=system_prompt,
    )

    pdf_path = 'files/Инфаркт миокарда.pdf'

    # embeddings = client.create_embeddings(texts)
    # print("Эмбеддинги:", embeddings)

    # Разбиение текста на части
    long_text = ""
    with open(pdf_path, 'rb') as pdf_file:
        pdf_processor = PDFProcessor(pdf_file)
        pdf_processor.process_pdf(start_page=0, end_page=pdf_processor.pages)
        for page_content in pdf_processor.extract():
            long_text += f"{page_content}\n"

    chunks = client.split_text_into_chunks(long_text, chunk_size=client.max_tokens)
    for i, chunk in enumerate(chunks):
        print("Количество токенов в части:", len(client.tokenize_text(chunk)))
    print("Количество страниц:", len(chunks))
    with open('result_2.md', 'a', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            print(f"--------- Page {i + 1} ----------")
            response = await client.send_message(chunk)
            f.write(f'{response}\n')


if __name__ == "__main__":
    asyncio.run(main())
