import tempfile
import os
from docx_parser import DocxParser

FIXTURES_DIR = os.path.join("tests", "docs")

class TestDocxParser:
    def test_file_not_found(self):
        parser = DocxParser("nonexistent.docx")
        try:
            parser.extract_text_and_comments()
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass
    
    def test_simple_comment(self):
        """Test basic comment extraction from simple_comment.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "simple_comment.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should extract the text
        assert "Hello world, this is a test." in text
        
        # Should have exactly 1 comment
        assert len(comments) == 1
        comment = comments[0]
        assert "This word needs clarification" in comment.text
        
        # Should have 1 comment range with correct position
        assert len(ranges) == 1
        range_obj = ranges[0]
        # Comment should be on "world" at positions 6-11
        assert range_obj.start_pos == 6
        assert range_obj.end_pos == 11
        assert text[range_obj.start_pos:range_obj.end_pos] == "world"
        
    def test_multiple_comments(self):
        """Test extraction of multiple comments from multiple_comments.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "multiple_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should extract the text
        assert "The quick brown fox jumps over the lazy dog." in text
        
        # Should have exactly 3 comments
        assert len(comments) == 3
        
        # Check comment texts contain expected content
        comment_texts = [c.text for c in comments]
        assert any("Too informal" in ct for ct in comment_texts)
        assert any("Be more specific" in ct for ct in comment_texts)
        assert any("Negative connotation" in ct for ct in comment_texts)
        
        # Should have 3 comment ranges with proper positions
        assert len(ranges) == 3
        # All ranges should be valid (start < end) 
        for r in ranges:
            assert r.start_pos < r.end_pos
            # Range should point to actual text
            commented_text = text[r.start_pos:r.end_pos]
            assert len(commented_text) > 0
    
    def test_same_text_multiple_comments(self):
        """Test multiple comments on the same text from same_text_multiple_comments.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "same_text_multiple_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Should extract the text
        assert "This phrase needs work badly." in text
        
        # Should have 2 comments on the same text
        assert len(comments) == 2
        
        comment_texts = [c.text for c in comments]
        assert any("Unclear" in ct for ct in comment_texts)
        assert any("requires improvement" in ct for ct in comment_texts)
        
        # Should have 2 ranges pointing to same text ("needs work")
        assert len(ranges) == 2
        # Both ranges should have same start/end positions
        assert ranges[0].start_pos == ranges[1].start_pos
        assert ranges[0].end_pos == ranges[1].end_pos
        # Should point to "needs work"
        commented_text = text[ranges[0].start_pos:ranges[0].end_pos]
        assert "needs work" == commented_text
    
    def test_point_comment(self):
        """Test point comments (no text range) from point_comment.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "point_comment.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        assert "Insert example here. More text follows." in text
        assert len(comments) == 1
        assert "Add specific example" in comments[0].text
        
        # Point comments should have start_pos == end_pos
        assert len(ranges) == 1
        assert ranges[0].start_pos == ranges[0].end_pos
    
    def test_overlapping_comments(self):
        """Test overlapping comment ranges from overlapping_comments.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "overlapping_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        assert "This complicated sentence structure is confusing." in text
        assert len(comments) == 2
        
        comment_texts = [c.text for c in comments]
        assert any("Too complex" in ct for ct in comment_texts)
        assert any("Restructure needed" in ct for ct in comment_texts)
        
        # Should have 2 overlapping ranges with proper positions
        assert len(ranges) == 2
        # Both ranges should be valid (start < end)
        for r in ranges:
            assert r.start_pos < r.end_pos
    
    def test_nested_comments(self):
        """Test nested comments from nested_comments.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "nested_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        assert "The really important section needs attention." in text
        assert len(comments) == 2
        
        comment_texts = [c.text for c in comments]
        assert any("Key part of document" in ct for ct in comment_texts)
        assert any("Define importance" in ct for ct in comment_texts)
        
        # Should have 2 ranges, one nested inside the other
        assert len(ranges) == 2
        # Verify nested relationship - one range should be inside the other
        ranges_sorted = sorted(ranges, key=lambda r: r.start_pos)
        outer, inner = ranges_sorted
        assert outer.start_pos <= inner.start_pos
        assert inner.end_pos <= outer.end_pos
    
    def test_multiline_comment_range(self):
        """Test comments spanning multiple paragraphs from multiline_comment_range.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "multiline_comment_range.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Text should contain both paragraphs
        assert "This paragraph has some text." in text
        assert "This second paragraph continues the thought." in text
        
        assert len(comments) == 1
        assert "This spans paragraphs" in comments[0].text
        
        # Should have proper start/end positions across paragraphs
        assert len(ranges) == 1
        range_obj = ranges[0]
        assert range_obj.start_pos != range_obj.end_pos  # Not a point comment
        assert range_obj.start_pos < range_obj.end_pos   # Valid range
    
    def test_edge_cases(self):
        """Test various edge cases from edge_cases.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "edge_cases.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        assert "Start text middle text end text" in text
        assert len(comments) == 3
        
        comment_texts = [c.text for c in comments]
        assert any("Weak beginning" in ct for ct in comment_texts)
        assert any("Better conclusion needed" in ct for ct in comment_texts)
        # Empty comment should still be extracted
        assert any(ct == "" for ct in comment_texts)
    
    def test_formatted_text(self):
        """Test comments on formatted text from formatted_text.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "formatted_text.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Text extraction should preserve text content even if formatting is lost
        assert "bold text" in text
        assert "italic text" in text
        
        assert len(comments) == 2
        comment_texts = [c.text for c in comments]
        assert any("Too emphatic" in ct for ct in comment_texts)
        assert any("Why italicized" in ct for ct in comment_texts)
    
    def test_no_comments_file(self):
        """Test file with no comments using no_comments.docx"""
        docx_path = os.path.join(FIXTURES_DIR, "no_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        assert len(comments) == 0
        assert len(ranges) == 0