import PyPDF2
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTRect, LTPage
import pdfplumber
from .tools import extract_table, text_extraction, table_converter
from typing import Dict, Any, List, Optional, BinaryIO


class PDFProcessor:
    def __init__(self, pdf_file: BinaryIO):
        """
        Initialize the PDFProcessor class.

        Args:
            pdf_file (BinaryIO): An opened binary file object for the PDF.
        """
        self.pdf_file = pdf_file
        self.text_per_page: Dict[int, Dict[str, Any]] = {}
        self.pdf_reader = PyPDF2.PdfReader(self.pdf_file)

    @property
    def pages(self):
        return len(self.pdf_reader.pages)

    def process_pdf(self, start_page: int = 0, end_page: Optional[int] = None) -> None:
        """
        Processes a range of pages in the PDF, extracting text and formatting.

        Args:
            start_page (int): The starting page number (0-indexed).
            end_page (Optional[int]): The ending page number (0-indexed, exclusive). If None, processes until the last page.
        """
        num_pages = self.pages

        # Если конечная страница не указана или превышает количество страниц, установить её на последнюю страницу
        if end_page is None or end_page > num_pages:
            end_page = num_pages

        # Получаем срез страниц как список PageObject
        pages_slice = self.pdf_reader.pages[start_page:end_page]

        # Обрабатываем каждую страницу в указанном срезе
        for page_num, page_text_obj in enumerate(pages_slice, start=start_page):
            # Используем pdfminer для более подробной обработки страницы
            for page in extract_pages(self.pdf_file, page_numbers=[page_num]):
                page_content = self.process_page(page_num, page)
                self.text_per_page[page_num] = page_content

    def process_page(self, pagenum: int, page: LTPage) -> Dict[str, Any]:
        """
        Processes a single page of the PDF, extracting text, tables, and formatting.

        Args:
            pagenum (int): The page number.
            page (LTPage): The page object from pdfminer.

        Returns:
            Dict[str, Any]: A dictionary with extracted text, formatting, and other page content.
        """
        page_text: List[str] = []
        line_format: List[str] = []
        text_from_images: List[str] = []
        text_from_tables: List[str] = []
        page_content: List[str] = []

        table_num = 0
        first_element = True
        table_extraction_flag = False

        # Используем pdfplumber для извлечения таблиц на указанной странице
        with pdfplumber.open(self.pdf_file) as pdf:
            page_tables = pdf.pages[pagenum]
            tables = page_tables.find_tables()

        page_elements = [(element.y1, element) for element in page._objs]
        page_elements.sort(key=lambda a: a[0], reverse=True)
        for i, component in enumerate(page_elements):
            pos = component[0]
            element = component[1]

            if isinstance(element, LTTextContainer):
                if not table_extraction_flag:
                    line_text, format_per_line = text_extraction(element)
                    page_text.append(line_text)
                    line_format.append(format_per_line)
                    page_content.append(line_text)

            if isinstance(element, LTRect):
                if first_element and (table_num + 1) <= len(tables):
                    lower_side = page.bbox[3] - tables[table_num].bbox[3]
                    upper_side = element.y1
                    table = extract_table(self.pdf_file, pagenum, table_num)
                    table_string = table_converter(table)
                    text_from_tables.append(table_string)
                    page_content.append(table_string)
                    table_extraction_flag = True
                    first_element = False
                    page_text.append('table')
                    line_format.append('table')

                    if element.y0 >= lower_side and element.y1 <= upper_side:
                        pass
                elif i + 1 < len(page_elements) and not isinstance(page_elements[i + 1][1], LTRect):
                    # Проверка на выход за пределы списка
                    table_extraction_flag = False
                    first_element = True
                    table_num += 1

        return {
            'text': page_text,
            'line_format': line_format,
            'text_from_images': text_from_images,
            'text_from_tables': text_from_tables,
            'page_content': page_content,
        }

    def extract(self):
        """
        Generator function that yields the extracted content for each page in the PDF, including text and tables.

        Yields:
            str: A formatted string for each page that includes the page key, text from tables,
                 and main text content, separated by spaces and followed by newlines for readability.

        Example:
            For each page in the PDF, this function will yield a formatted string in the following format:
                "Page_X <table_text_1> <table_text_2> ... <text_line_1> <text_line_2> ..."
        """
        for key, value in self.text_per_page.items():
            yield ' '.join(value['text_from_tables'] + value['text'])
