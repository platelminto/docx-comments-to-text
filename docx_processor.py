from pathlib import Path
from typing import Union
from docx_parser import DocxParser
from text_formatter import format_text_with_comments


def process_docx(input_file: Union[str, Path], authors: str = 'auto') -> str:
    """
    Extract comments from a DOCX file and return formatted text with inline comments.
    
    Args:
        input_file: Path to the DOCX file
        authors: How to display authors ('never', 'always', 'auto')
        
    Returns:
        Formatted text with inline comments
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        Exception: If processing fails
    """
    # Parse the DOCX file
    parser = DocxParser(str(input_file))
    text, comments, ranges = parser.extract_text_and_comments()
    
    # Format text with comments
    formatted_text = format_text_with_comments(text, comments, ranges, show_authors=authors)
    
    return formatted_text