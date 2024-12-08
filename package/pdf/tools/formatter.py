from typing import List, Optional

import pdfplumber
from pdfminer.layout import (
    LTChar,
    LTTextBoxHorizontal,
    LTTextContainer,
)

TableType = List[List[Optional[str]]]


def text_extraction(element: LTTextBoxHorizontal) -> (str, list):
    """
    Function for extraction text from pdf page.
    Args:
        element: TextBox element from pdfminer library.

    Returns: Two value. Text in current page and all format text in page.
    """
    line_text = element.get_text()
    line_formats = []
    for text_line in element:
        if not isinstance(text_line, LTTextContainer):
            continue
        for character in text_line:
            if not isinstance(character, LTChar):
                continue
            line_formats.append(character.fontname)
            line_formats.append(character.size)
            line_formats.append(f'upright - {character.upright}')
            line_formats.append(f'adv - {character.adv}')

    return line_text, list(set(line_formats))


def extract_table(pdf_path: str, page_num: int, table_num: int) -> TableType:
    """
    Function for get text from tables from pdf document.
    Args:
        pdf_path: path to pdf file.
        page_num: num pdf page.
        table_num: num table in pdf document.

    Returns: Data of tables.

    """
    pdf = pdfplumber.open(pdf_path)
    table_page = pdf.pages[page_num]
    table = table_page.extract_tables()[table_num]
    return table


def table_converter(table: TableType) -> str:
    """
    Function for convert table view to text.
    Args:
        table: Table object (pandas table object)

    Returns: String view of table in pdf file.

    """
    table_string = ''
    for row_num in range(len(table)):
        row = table[row_num]
        cleaned_row = [
            item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item
            in row]
        table_string += ('|' + '|'.join(cleaned_row) + '|' + '\n')
    table_string = table_string[:-1]
    return table_string
