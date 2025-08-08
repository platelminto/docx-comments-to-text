import os
from docx_parser import DocxParser
from text_formatter import format_text_with_comments

FIXTURES_DIR = os.path.join("tests", "docs")

class TestNewlinePreservation:
    def test_multiline_document_preserves_newlines(self):
        """Test that multiline documents preserve paragraph breaks as newlines"""
        docx_path = os.path.join(FIXTURES_DIR, "multiline_comment_range.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should preserve newlines between paragraphs
        assert "\n" in text, "Expected newlines to be preserved between paragraphs"
        
        # Should not have consecutive text without separation
        assert "text.This second" not in text, "Paragraphs should be separated by newlines"
    
    def test_formatted_text_preserves_newlines(self):
        """Test that formatted text with comments preserves original newlines"""
        docx_path = os.path.join(FIXTURES_DIR, "multiline_comment_range.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        formatted_text = format_text_with_comments(text, comments, ranges)
        
        # Should still have newlines in formatted output
        assert "\n" in formatted_text, "Formatted text should preserve newlines"
    
    def test_single_paragraph_no_extra_newlines(self):
        """Test that single paragraph documents don't get extra newlines"""
        docx_path = os.path.join(FIXTURES_DIR, "simple_comment.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should not have newlines in single paragraph
        assert text.count("\n") == 0, "Single paragraph should not contain newlines"
    
    def test_comment_positions_account_for_newlines(self):
        """Test that comment positions are correct when newlines are preserved"""
        docx_path = os.path.join(FIXTURES_DIR, "multiline_comment_range.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Comment positions should be valid for the text with newlines
        for range_obj in ranges:
            assert 0 <= range_obj.start_pos <= len(text), f"Start position {range_obj.start_pos} out of bounds for text length {len(text)}"
            assert 0 <= range_obj.end_pos <= len(text), f"End position {range_obj.end_pos} out of bounds for text length {len(text)}"
            assert range_obj.start_pos <= range_obj.end_pos, "Start position should be <= end position"
    
    def test_multiline_comment_content_preserved(self):
        """Test that comments with newlines preserve them during extraction"""
        docx_path = os.path.join(FIXTURES_DIR, "multiline_comment_content.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should extract at least one comment
        assert len(comments) >= 1, "Should extract at least one comment"
        
        # At least one comment should contain newlines
        multiline_comments = [c for c in comments if '\n' in c.text]
        assert len(multiline_comments) > 0, "Should have at least one comment with newlines"
        
        # Check that newlines are preserved in comment text
        multiline_comment = multiline_comments[0]
        lines = multiline_comment.text.split('\n')
        assert len(lines) > 1, f"Comment should have multiple lines, got: {repr(multiline_comment.text)}"