import asyncio

from pydantic import SecretStr

from package.openai import PromptManager
from package.openai.client import ChatGPTClient
from internal.config import settings
from package.pdf import PDFProcessor

from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

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

    pdf = MarkdownPdf(toc_level=3)
    pdf_path = 'files/Инфаркт миокарда.pdf'

    # embeddings = client.create_embeddings(texts)
    # print("Эмбеддинги:", embeddings)

    long_text = ''
    texts = ''
    with open(pdf_path, 'rb') as pdf_file:
        pdf_processor = PDFProcessor(pdf_file)
        pdf_processor.process_pdf(start_page=0, end_page=pdf_processor.pages)
        for page_content in pdf_processor.extract():
            long_text += f"{page_content}\n"

    chunks = client.split_text_into_chunks(long_text, chunk_size=client.max_tokens)
    print("Количество страниц:", len(chunks))

    for i, chunk in enumerate(chunks):
        print(f"--------- Page {i + 1} ----------")
        response = await client.send_message(chunk)
        texts += response

    pdf.add_section(Section(texts, toc=False))
    pdf.save("result_1.pdf")


if __name__ == "__main__":
    asyncio.run(main())
