"""Extract reviewer comments from .docx files and insert them inline with the text."""

from .docx_parser import DocxParser, Comment, CommentRange
from .docx_processor import process_docx
from .text_formatter import format_text_with_comments

__all__ = ['DocxParser', 'Comment', 'CommentRange', 'process_docx', 'format_text_with_comments']