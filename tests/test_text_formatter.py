import os
from docx_parser import DocxParser, Comment, CommentRange
from text_formatter import format_text_with_comments, _format_comment

FIXTURES_DIR = os.path.join("tests", "docs")

class TestTextFormatter:
    def test_simple_range_comment(self):
        """Test formatting a single range comment"""
        text = "Hello world, this is a test."
        comments = [Comment(id="1", author="Reviewer", text="This word needs clarification")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        result = format_text_with_comments(text, comments, ranges)
        comment_part = _format_comment(comments[0], False)  # Auto mode with single author = no author
        expected = f"Hello [world] {comment_part}, this is a test."
        assert result == expected

    def test_point_comment(self):
        """Test formatting a point comment (no text range)"""
        text = "Insert example here. More text follows."
        comments = [Comment(id="1", author="Reviewer", text="Add specific example")]
        ranges = [CommentRange(comment_id="1", start_pos=19, end_pos=19)]
        
        result = format_text_with_comments(text, comments, ranges)
        comment_part = _format_comment(comments[0], False)  # Auto mode with single author = no author
        expected = f"Insert example here{comment_part}. More text follows."
        assert result == expected

    def test_multiple_comments_different_ranges(self):
        """Test multiple comments on different text ranges"""
        text = "The quick brown fox jumps over the lazy dog."
        comments = [
            Comment(id="1", author="Reviewer", text="Too informal"),
            Comment(id="2", author="Reviewer", text="Be more specific"),
            Comment(id="3", author="Reviewer", text="Negative connotation")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=4, end_pos=9),   # "quick"
            CommentRange(comment_id="2", start_pos=16, end_pos=19), # "fox"
            CommentRange(comment_id="3", start_pos=35, end_pos=39)  # "lazy"
        ]
        
        result = format_text_with_comments(text, comments, ranges)
        # Comments should appear in reverse order due to position-based insertion
        expected = "The [quick] [COMMENT: \"Too informal\"] brown [fox] [COMMENT: \"Be more specific\"] jumps over the [lazy] [COMMENT: \"Negative connotation\"] dog."
        assert result == expected

    def test_overlapping_comments_same_range(self):
        """Test multiple comments on the same text range"""
        text = "This phrase needs work badly."
        comments = [
            Comment(id="1", author="Reviewer1", text="Unclear"),
            Comment(id="2", author="Reviewer2", text="This phrase requires improvement")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=12, end_pos=22), # "needs work"
            CommentRange(comment_id="2", start_pos=12, end_pos=22)  # "needs work"
        ]
        
        result = format_text_with_comments(text, comments, ranges)
        # Both comments should appear, order may vary based on implementation
        assert "[needs work]" in result
        # Auto mode with multiple authors = show authors
        comment1 = _format_comment(comments[0], True)  # Multiple authors = True
        comment2 = _format_comment(comments[1], True)  # Multiple authors = True
        assert comment1 in result
        assert comment2 in result

    def test_mixed_point_and_range_comments(self):
        """Test combination of point and range comments"""
        text = "Start here. End there."
        comments = [
            Comment(id="1", author="Reviewer", text="Range comment"),
            Comment(id="2", author="Reviewer", text="Point comment")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=0, end_pos=5),   # "Start"
            CommentRange(comment_id="2", start_pos=11, end_pos=11) # Point at "."
        ]
        
        result = format_text_with_comments(text, comments, ranges)
        range_comment = _format_comment(comments[0], False)  # Single author = no author
        point_comment = _format_comment(comments[1], False)  # Single author = no author
        expected = f"[Start] {range_comment} here.{point_comment} End there."
        assert result == expected

    def test_no_comments(self):
        """Test formatting text with no comments"""
        text = "Plain text with no comments."
        result = format_text_with_comments(text, [], [])
        assert result == text

    def test_comment_not_found(self):
        """Test handling of ranges with missing comments"""
        text = "Hello world"
        comments = []  # No comments
        ranges = [CommentRange(comment_id="missing", start_pos=6, end_pos=11)]
        
        result = format_text_with_comments(text, comments, ranges)
        # Should return original text since comment is missing
        assert result == text

    def test_integration_with_simple_comment_docx(self):
        """Test end-to-end formatting with actual docx file"""
        docx_path = os.path.join(FIXTURES_DIR, "simple_comment.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        result = format_text_with_comments(text, comments, ranges)
        
        # Should contain bracketed commented text and comment
        assert "[world]" in result
        assert "[COMMENT:" in result
        assert "This word needs clarification" in result

    def test_integration_with_multiple_comments_docx(self):
        """Test end-to-end formatting with multiple comments docx"""
        docx_path = os.path.join(FIXTURES_DIR, "multiple_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        result = format_text_with_comments(text, comments, ranges)
        
        # Should have 3 sets of brackets and comments
        bracket_count = result.count('[') - result.count('[COMMENT:')
        assert bracket_count == 3  # 3 bracketed text pieces
        assert result.count('[COMMENT:') == 3  # 3 comments

    def test_integration_with_point_comment_docx(self):
        """Test end-to-end formatting with point comment docx"""
        docx_path = os.path.join(FIXTURES_DIR, "point_comment.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        result = format_text_with_comments(text, comments, ranges)
        
        # Should contain point comment but no bracketed text
        assert "[COMMENT:" in result
        assert "Add specific example" in result
        # Should not have any bracketed text since it's a point comment
        bracket_count = result.count('[') - result.count('[COMMENT:')
        assert bracket_count == 0

    def test_integration_with_nested_comments_docx(self):
        """Test end-to-end formatting with nested/overlapping comments"""
        docx_path = os.path.join(FIXTURES_DIR, "nested_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        result = format_text_with_comments(text, comments, ranges)
        
        # Should properly handle overlapping ranges without corruption
        # The outer range "really important section" should be fully bracketed
        # The inner range "important" should also be properly bracketed
        assert "[really [important]" in result or "[really important]" in result
        assert "Define importance" in result
        assert "Key part of document" in result
        # Should not have corrupted output like "[COMM] [COMMENT"
        assert "[COMM]" not in result
        assert result.count("[COMMENT:") == 2

    def test_integration_with_nested_comments_end_paragraph(self):
        """Test end-paragraph placement with nested/overlapping comments"""
        docx_path = os.path.join(FIXTURES_DIR, "nested_comments.docx")
        parser = DocxParser(docx_path)
        text, comments, ranges = parser.extract_text_and_comments()
        
        result = format_text_with_comments(text, comments, ranges, placement="end-paragraph")
        
        # Should have clean text without broken markers in the middle of words
        # Should not have broken markers like "sect[1]ion"
        assert "sect[1]ion" not in result
        # Should have properly positioned markers in numerical order (left to right)
        assert "The really important[1] section[2] needs attention." in result
        # Should have proper numbered comments
        assert "Comments:" in result
        assert "1." in result and "2." in result
        # Comments should be numbered by end position for left-to-right marker ordering
        # Comment on "important" (ends first) should be #1
        # Comment on "really important section" (ends second) should be #2
        assert "1. Define importance" in result
        assert "2. Key part of document" in result

class TestAuthorDisplay:
    def test_show_authors_never(self):
        """Test never showing authors"""
        text = "Hello world"
        comments = [Comment(id="1", author="John", text="needs work")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="never")
        comment_part = _format_comment(comments[0], False)
        expected = f"Hello [world] {comment_part}"
        assert result == expected

    def test_show_authors_always_single_author(self):
        """Test always showing authors even with single author"""
        text = "Hello world"
        comments = [Comment(id="1", author="John", text="needs work")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="always")
        comment_part = _format_comment(comments[0], True)
        expected = f"Hello [world] {comment_part}"
        assert result == expected

    def test_show_authors_always_multiple_authors(self):
        """Test always showing authors with multiple authors"""
        text = "Hello world"
        comments = [
            Comment(id="1", author="John", text="needs work"),
            Comment(id="2", author="Jane", text="unclear")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=6, end_pos=11),
            CommentRange(comment_id="2", start_pos=6, end_pos=11)
        ]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="always")
        comment1 = _format_comment(comments[0], True)
        comment2 = _format_comment(comments[1], True)
        assert comment1 in result
        assert comment2 in result

    def test_show_authors_auto_single_author(self):
        """Test auto mode with single author (should hide author)"""
        text = "Hello world"
        comments = [Comment(id="1", author="John", text="needs work")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="auto")
        comment_part = _format_comment(comments[0], False)
        expected = f"Hello [world] {comment_part}"
        assert result == expected
        assert "John:" not in result

    def test_show_authors_auto_multiple_authors(self):
        """Test auto mode with multiple authors (should show authors)"""
        text = "Hello world"
        comments = [
            Comment(id="1", author="John", text="needs work"),
            Comment(id="2", author="Jane", text="unclear")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=6, end_pos=11),
            CommentRange(comment_id="2", start_pos=6, end_pos=11)
        ]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="auto")
        comment1 = _format_comment(comments[0], True)  # Multiple authors = True
        comment2 = _format_comment(comments[1], True)  # Multiple authors = True
        assert comment1 in result
        assert comment2 in result

    def test_show_authors_auto_same_author_multiple_comments(self):
        """Test auto mode with same author having multiple comments (should hide author)"""
        text = "Hello world test"
        comments = [
            Comment(id="1", author="John", text="needs work"),
            Comment(id="2", author="John", text="also unclear")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=6, end_pos=11),  # "world"
            CommentRange(comment_id="2", start_pos=12, end_pos=16)  # "test"
        ]
        
        result = format_text_with_comments(text, comments, ranges, show_authors="auto")
        assert "John:" not in result
        assert "needs work" in result
        assert "also unclear" in result

    def test_default_show_authors_parameter(self):
        """Test that show_authors defaults to 'auto'"""
        text = "Hello world"
        comments = [Comment(id="1", author="John", text="needs work")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        # Call without show_authors parameter (should default to "auto")
        result = format_text_with_comments(text, comments, ranges)
        comment_part = _format_comment(comments[0], False)  # Auto with single author = False
        expected = f"Hello [world] {comment_part}"
        assert result == expected

    def test_show_authors_point_comments(self):
        """Test author display with point comments"""
        text = "Insert here."
        comments = [Comment(id="1", author="Jane", text="Add example")]
        ranges = [CommentRange(comment_id="1", start_pos=7, end_pos=7)]
        
        result_never = format_text_with_comments(text, comments, ranges, show_authors="never")
        result_always = format_text_with_comments(text, comments, ranges, show_authors="always")
        
        comment_never = _format_comment(comments[0], False)
        comment_always = _format_comment(comments[0], True)
        
        assert comment_never in result_never
        assert "Jane:" not in result_never
        assert comment_always in result_always


class TestPlacementOptions:
    def test_end_paragraph_placement_single_paragraph(self):
        """Test end-paragraph placement with single paragraph"""
        text = "This is a sentence. This is another sentence."
        comments = [
            Comment(id="1", author="Reviewer", text="First comment"),
            Comment(id="2", author="Reviewer", text="Second comment")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=5, end_pos=7),   # "is"
            CommentRange(comment_id="2", start_pos=28, end_pos=35)  # "another"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="end-paragraph")
        
        # Should have numbered markers in text
        assert "This is[1] a sentence. This is another[2] sentence." in result
        # Comments should appear at end with numbers
        assert "Comments:" in result
        assert "1. First comment" in result
        assert "2. Second comment" in result

    def test_end_paragraph_placement_multiple_paragraphs(self):
        """Test end-paragraph placement with multiple paragraphs"""
        text = "First paragraph with comment.\n\nSecond paragraph also has feedback."
        comments = [
            Comment(id="1", author="Reviewer", text="Paragraph 1 feedback"),
            Comment(id="2", author="Reviewer", text="Paragraph 2 feedback")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=21, end_pos=28),  # "comment"
            CommentRange(comment_id="2", start_pos=57, end_pos=65)   # "feedback"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="end-paragraph")
        
        # Should have numbered markers in each paragraph
        assert "First paragraph with comment[1]." in result
        assert "Second paragraph also has feedback[2]." in result
        assert "Comments:" in result
        assert "1. Paragraph 1 feedback" in result
        assert "2. Paragraph 2 feedback" in result

    def test_end_paragraph_placement_point_comments(self):
        """Test end-paragraph placement with point comments"""
        text = "Insert example here. More text follows."
        comments = [Comment(id="1", author="Reviewer", text="Add specific example")]
        ranges = [CommentRange(comment_id="1", start_pos=19, end_pos=19)]  # Point comment
        
        result = format_text_with_comments(text, comments, ranges, placement="end-paragraph")
        
        # Should have marker at point position
        assert "Insert example here[1]. More text follows." in result
        assert "Comments:" in result
        assert "1. [Position]: Add specific example" in result

    def test_end_paragraph_placement_with_authors(self):
        """Test end-paragraph placement shows authors correctly"""
        text = "Text with multiple reviewers."
        comments = [
            Comment(id="1", author="John", text="First feedback"),
            Comment(id="2", author="Jane", text="Second feedback")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=5, end_pos=9),   # "with"
            CommentRange(comment_id="2", start_pos=19, end_pos=28)  # "reviewers"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="end-paragraph", show_authors="always")
        
        assert "Text with[1] multiple reviewers[2]." in result
        assert "Comments:" in result
        assert "1. John: First feedback" in result
        assert "2. Jane: Second feedback" in result

    def test_comments_only_placement(self):
        """Test comments-only placement extracts just feedback"""
        text = "This is original text with comments."
        comments = [
            Comment(id="1", author="Reviewer1", text="First feedback"),
            Comment(id="2", author="Reviewer2", text="Second feedback"),
            Comment(id="3", author="Reviewer1", text="Third feedback")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=5, end_pos=7),   # "is"
            CommentRange(comment_id="2", start_pos=17, end_pos=21), # "text"
            CommentRange(comment_id="3", start_pos=27, end_pos=35)  # "comments"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="comments-only")
        
        # Should only contain comments, no original text
        assert "This is original text with comments." not in result
        assert "First feedback" in result
        assert "Second feedback" in result
        assert "Third feedback" in result

    def test_comments_only_with_context(self):
        """Test comments-only placement includes text context"""
        text = "Context for understanding feedback."
        comments = [
            Comment(id="1", author="Reviewer", text="Needs more detail"),
            Comment(id="2", author="Reviewer", text="Unclear phrasing")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=0, end_pos=7),   # "Context"
            CommentRange(comment_id="2", start_pos=26, end_pos=34)  # "feedback"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="comments-only")
        
        # Should show commented text for context
        assert '"Context": Needs more detail' in result
        assert '"feedback": Unclear phrasing' in result
        assert "Context for understanding feedback." not in result

    def test_comments_only_point_comments(self):
        """Test comments-only placement with point comments"""
        text = "Text with insertion point."
        comments = [Comment(id="1", author="Reviewer", text="Add example here")]
        ranges = [CommentRange(comment_id="1", start_pos=15, end_pos=15)]
        
        result = format_text_with_comments(text, comments, ranges, placement="comments-only")
        
        assert "[Position 15]: Add example here" in result
        assert "Text with insertion point." not in result

    def test_comments_only_with_authors_always(self):
        """Test comments-only placement with authors always shown"""
        text = "Text with single author comment."
        comments = [Comment(id="1", author="John", text="Single author feedback")]
        ranges = [CommentRange(comment_id="1", start_pos=5, end_pos=9)]  # "with"
        
        result = format_text_with_comments(text, comments, ranges, placement="comments-only", show_authors="always")
        
        assert '"with": John: Single author feedback' in result
        assert "Text with single author comment." not in result

    def test_comments_only_with_authors_never(self):
        """Test comments-only placement with authors never shown"""
        text = "Text with multiple author comments."
        comments = [
            Comment(id="1", author="John", text="First feedback"),
            Comment(id="2", author="Jane", text="Second feedback")
        ]
        ranges = [
            CommentRange(comment_id="1", start_pos=5, end_pos=9),   # "with"
            CommentRange(comment_id="2", start_pos=19, end_pos=25)  # "author"
        ]
        
        result = format_text_with_comments(text, comments, ranges, placement="comments-only", show_authors="never")
        
        assert '"with": First feedback' in result
        assert '"author": Second feedback' in result
        assert "John:" not in result
        assert "Jane:" not in result

    def test_inline_placement_unchanged(self):
        """Test that inline placement works as before (default behavior)"""
        text = "Hello world"
        comments = [Comment(id="1", author="Reviewer", text="needs work")]
        ranges = [CommentRange(comment_id="1", start_pos=6, end_pos=11)]
        
        result_explicit = format_text_with_comments(text, comments, ranges, placement="inline")
        result_default = format_text_with_comments(text, comments, ranges)
        
        # Both should produce same result
        assert result_explicit == result_default
        assert result_explicit == 'Hello [world] [COMMENT: "needs work"]'