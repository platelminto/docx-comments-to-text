import zipfile
from xml.etree import ElementTree as ET
from dataclasses import dataclass
from typing import List

@dataclass
class Comment:
    id: str
    author: str
    text: str

@dataclass(frozen=True)
class CommentRange:
    comment_id: str
    start_pos: int
    end_pos: int

class DocxParser:
    # DOCX XML namespaces
    WORD_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    
    def __init__(self, docx_path: str):
        self.docx_path = docx_path

    def extract_text_and_comments(self) -> tuple[str, List[Comment], List[CommentRange]]:
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as docx:
                document_xml = docx.read('word/document.xml')
                
                comments_xml = None
                try:
                    comments_xml = docx.read('word/comments.xml')
                except KeyError:
                    pass
                
                # Extract text and ranges together to ensure consistent positioning
                text, ranges = self._extract_text_and_ranges(document_xml) if comments_xml else (self._extract_text(document_xml), [])
                comments = self._extract_comments(comments_xml) if comments_xml else []
                
                return text, comments, ranges
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file: {self.docx_path}")

    def _extract_text(self, document_xml: bytes) -> str:
        tree = ET.fromstring(document_xml)
        text_parts = []
        current_paragraph = None
        
        for elem in tree.iter():
            # Handle paragraph breaks
            if elem.tag == f'{self.WORD_NS}p':
                if current_paragraph is not None and text_parts:
                    text_parts.append('\n')
                current_paragraph = elem
            elif elem.tag == f'{self.WORD_NS}t' and elem.text:
                text_parts.append(elem.text)
        
        return ''.join(text_parts)

    def _extract_comments(self, comments_xml: bytes) -> List[Comment]:
        tree = ET.fromstring(comments_xml)
        comments = []
        
        for comment_elem in tree.iter():
            if comment_elem.tag == f'{self.WORD_NS}comment':
                comment_id = comment_elem.get(f'{self.WORD_NS}id')
                author = comment_elem.get(f'{self.WORD_NS}author', '')
                
                text_parts = []
                current_paragraph = None
                for text_elem in comment_elem.iter():
                    # Handle paragraph breaks in comments
                    if text_elem.tag == f'{self.WORD_NS}p':
                        if current_paragraph is not None and text_parts:
                            text_parts.append('\n')
                        current_paragraph = text_elem
                    elif text_elem.tag == f'{self.WORD_NS}t' and text_elem.text:
                        text_parts.append(text_elem.text)
                
                comment_text = ''.join(text_parts)
                comments.append(Comment(id=comment_id, author=author, text=comment_text))
        
        return comments

    def _extract_text_and_ranges(self, document_xml: bytes) -> tuple[str, List[CommentRange]]:
        tree = ET.fromstring(document_xml)
        text_parts = []
        ranges = []
        position = 0
        comment_starts = {}  # comment_id -> start_position
        current_paragraph = None
        
        # Walk through document in document order to track positions
        for elem in tree.iter():
            # Handle paragraph breaks - add newline when we finish a paragraph
            if elem.tag == f'{self.WORD_NS}p':
                if current_paragraph is not None and text_parts:
                    # Add newline at end of previous paragraph (if we had content)
                    text_parts.append('\n')
                    position += 1
                current_paragraph = elem
            
            # Handle comment range start markers
            elif elem.tag == f'{self.WORD_NS}commentRangeStart':
                comment_id = elem.get(f'{self.WORD_NS}id')
                comment_starts[comment_id] = position
            
            # Handle comment range end markers
            elif elem.tag == f'{self.WORD_NS}commentRangeEnd':
                comment_id = elem.get(f'{self.WORD_NS}id')
                if comment_id in comment_starts:
                    start_pos = comment_starts[comment_id]
                    ranges.append(CommentRange(
                        comment_id=comment_id,
                        start_pos=start_pos,
                        end_pos=position
                    ))
                    del comment_starts[comment_id]
            
            # Handle point comments (commentReference elements)
            # Only create point comments for references that don't have ranges
            elif elem.tag == f'{self.WORD_NS}commentReference':
                comment_id = elem.get(f'{self.WORD_NS}id')
                if comment_id:
                    # Check if this comment already has a range
                    existing_range = any(r.comment_id == comment_id for r in ranges)
                    if not existing_range:
                        ranges.append(CommentRange(
                            comment_id=comment_id,
                            start_pos=position,
                            end_pos=position
                        ))
            
            # Handle text elements and track position
            elif elem.tag == f'{self.WORD_NS}t' and elem.text:
                text_parts.append(elem.text)
                position += len(elem.text)
        
        # Handle any remaining unclosed comment starts (point comments)
        for comment_id, start_pos in comment_starts.items():
            ranges.append(CommentRange(
                comment_id=comment_id,
                start_pos=start_pos,
                end_pos=start_pos
            ))
        
        text = ''.join(text_parts)
        return text, ranges

    def _extract_comment_ranges(self, document_xml: bytes) -> List[CommentRange]:
        tree = ET.fromstring(document_xml)
        ranges = []
        
        # Track position as we traverse the document
        position = 0
        comment_starts = {}  # comment_id -> start_position
        
        # First pass: build position mapping by traversing in document order
        for elem in tree.iter():
            # Add text length to position counter
            if elem.tag == f'{self.WORD_NS}t' and elem.text:
                text_length = len(elem.text)
                
                # Check for comment range start before text
                parent = elem.getparent()
                if parent is not None:
                    for sibling in parent:
                        if sibling.tag == f'{self.WORD_NS}commentRangeStart':
                            comment_id = sibling.get(f'{self.WORD_NS}id')
                            if comment_id not in comment_starts:
                                comment_starts[comment_id] = position
                        elif sibling.tag == f'{self.WORD_NS}commentRangeEnd':
                            comment_id = sibling.get(f'{self.WORD_NS}id')
                            if comment_id in comment_starts:
                                start_pos = comment_starts[comment_id]
                                ranges.append(CommentRange(
                                    comment_id=comment_id, 
                                    start_pos=start_pos, 
                                    end_pos=position + text_length
                                ))
                                del comment_starts[comment_id]
                        elif sibling == elem:
                            # We've reached the text element, update position
                            position += text_length
                            break
                else:
                    position += text_length
            
            # Handle comment range markers
            elif elem.tag == f'{self.WORD_NS}commentRangeStart':
                comment_id = elem.get(f'{self.WORD_NS}id')
                comment_starts[comment_id] = position
                
            elif elem.tag == f'{self.WORD_NS}commentRangeEnd':
                comment_id = elem.get(f'{self.WORD_NS}id')
                if comment_id in comment_starts:
                    start_pos = comment_starts[comment_id]
                    ranges.append(CommentRange(
                        comment_id=comment_id, 
                        start_pos=start_pos, 
                        end_pos=position
                    ))
                    del comment_starts[comment_id]
        
        # Handle any remaining point comments (same start and end position)
        for comment_id, start_pos in comment_starts.items():
            ranges.append(CommentRange(
                comment_id=comment_id,
                start_pos=start_pos,
                end_pos=start_pos
            ))
        
        return ranges