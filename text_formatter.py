from typing import List
from docx_parser import Comment, CommentRange

def format_text_with_comments(text: str, comments: List[Comment], ranges: List[CommentRange], show_authors: str = "auto", placement: str = "inline") -> str:
    """
    Format text by inserting comments with configurable placement options.
    
    Args:
        text: Original document text
        comments: List of Comment objects
        ranges: List of CommentRange objects mapping comments to text positions
        show_authors: "never", "always", or "auto" (default: "auto")
                     - "never": never show authors
                     - "always": always show authors as "Author: text"
                     - "auto": show authors only when multiple authors exist
        placement: "inline", "end-paragraph", or "comments-only" (default: "inline")
                  - "inline": [commented text] [COMMENT: "feedback"] (current behavior)
                  - "end-paragraph": clean text with comments grouped at end of each paragraph
                  - "comments-only": extract only comments with text context
        
    Returns:
        Formatted text according to placement option
    """
    if not ranges:
        return text
    
    # Dispatch to appropriate formatting function based on placement
    if placement == "inline":
        return _format_inline(text, comments, ranges, show_authors)
    elif placement == "end-paragraph":
        return _format_end_paragraph(text, comments, ranges, show_authors)
    elif placement == "comments-only":
        return _format_comments_only(text, comments, ranges, show_authors)
    else:
        raise ValueError(f"Unknown placement option: {placement}. Valid options: inline, end-paragraph, comments-only")


def _should_show_authors(show_authors: str, comments: List[Comment]) -> bool:
    """Determine if authors should be shown based on the mode and comment data."""
    if show_authors == "never":
        return False
    elif show_authors == "always":
        return True
    elif show_authors == "auto":
        # Show authors only if there are multiple unique authors
        authors = {comment.author for comment in comments}
        return len(authors) > 1
    else:
        # Default to "auto" for unknown modes
        authors = {comment.author for comment in comments}
        return len(authors) > 1


def _format_comment(comment: Comment, show_author: bool) -> str:
    """Format a single comment with optional author."""
    if show_author and comment.author:
        return f'[COMMENT {comment.author}: "{comment.text}"]'
    else:
        return f'[COMMENT: "{comment.text}"]'


def _format_inline(text: str, comments: List[Comment], ranges: List[CommentRange], show_authors: str) -> str:
    """Format text with inline comments (original behavior)."""
    if not ranges:
        return text
        
    # Create comment lookup map
    comment_map = {c.id: c for c in comments}
    
    # Determine if we should show authors
    should_show_authors = _should_show_authors(show_authors, comments)
    
    # Build nested structure by processing ranges from outermost to innermost
    result = _build_nested_inline(text, ranges, comment_map, should_show_authors)
    
    return result


def _build_nested_inline(text: str, ranges: List[CommentRange], comment_map: dict, should_show_authors: bool) -> str:
    """Build inline text with properly nested comments using event-based approach."""
    if not ranges:
        return text
    
    # Create events for range starts and ends
    events = []
    for range_obj in ranges:
        comment = comment_map.get(range_obj.comment_id)
        if not comment:
            continue
            
        if range_obj.start_pos == range_obj.end_pos:
            # Point comment
            comment_text = _format_comment(comment, should_show_authors)
            events.append((range_obj.start_pos, 'point', comment_text))
        else:
            # Range comment
            comment_text = _format_comment(comment, should_show_authors)
            events.append((range_obj.start_pos, 'start', range_obj))
            events.append((range_obj.end_pos, 'end', range_obj, comment_text))
    
    # Sort events by position, with starts before ends at the same position
    events.sort(key=lambda x: (x[0], x[1] == 'end'))
    
    result = []
    last_pos = 0
    
    for event in events:
        pos = event[0]
        event_type = event[1]
        
        # Add text up to this position
        result.append(text[last_pos:pos])
        
        if event_type == 'point':
            comment_text = event[2]
            result.append(comment_text)
        elif event_type == 'start':
            result.append('[')
        elif event_type == 'end':
            comment_text = event[3]
            result.append(f'] {comment_text}')
        
        last_pos = pos
    
    # Add remaining text
    result.append(text[last_pos:])
    
    return ''.join(result)


def _format_end_paragraph(text: str, comments: List[Comment], ranges: List[CommentRange], show_authors: str) -> str:
    """Format text with numbered markers and comments grouped at end of each paragraph."""
    # Create comment lookup map
    comment_map = {c.id: c for c in comments}
    
    # Determine if we should show authors
    should_show_authors = _should_show_authors(show_authors, comments)
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    
    # Track character positions across paragraphs and global comment counter
    char_offset = 0
    comment_counter = 1
    result_paragraphs = []
    
    for paragraph in paragraphs:
        para_start = char_offset
        para_end = char_offset + len(paragraph)
        
        # Find comments that fall within this paragraph
        para_ranges = []
        for range_obj in ranges:
            comment = comment_map.get(range_obj.comment_id)
            if comment and para_start <= range_obj.start_pos < para_end:
                para_ranges.append(range_obj)
        
        # First, assign numbers based on end position order (for left-to-right marker appearance)
        para_ranges_by_end = sorted(para_ranges, key=lambda r: r.end_pos)
        range_to_number = {}
        para_comments = []
        
        for range_obj in para_ranges_by_end:
            comment = comment_map.get(range_obj.comment_id)
            if not comment:
                continue
                
            range_to_number[range_obj] = comment_counter
            
            if range_obj.start_pos == range_obj.end_pos:
                # Point comment
                para_comments.append((comment_counter, f'[Position]: {_format_comment_text(comment, should_show_authors)}'))
            else:
                # Range comment
                para_comments.append((comment_counter, _format_comment_text(comment, should_show_authors)))
            
            comment_counter += 1
        
        # Insert markers for all ranges, but use event-based approach like inline
        # to handle overlapping ranges correctly
        events = []
        for range_obj in para_ranges:
            if range_obj not in range_to_number:
                continue
                
            number = range_to_number[range_obj]
            marker = f'[{number}]'
            
            # Calculate position relative to paragraph start
            rel_start = range_obj.start_pos - para_start
            rel_end = range_obj.end_pos - para_start
            
            if range_obj.start_pos == range_obj.end_pos:
                # Point comment - insert marker at position
                events.append((rel_start, 'point', marker, number))
            else:
                # Range comment - insert marker after the range
                events.append((rel_end, 'marker', marker, number))
        
        # Sort events by position, then by marker number for consistent ordering
        events.sort(key=lambda x: (x[0], x[3]))
        
        # Build modified paragraph with markers
        modified_paragraph = ""
        last_pos = 0
        
        for pos, event_type, marker, number in events:
            # Add text up to this position
            modified_paragraph += paragraph[last_pos:pos]
            # Add marker
            modified_paragraph += marker
            last_pos = pos
        
        # Add remaining text
        modified_paragraph += paragraph[last_pos:]
        
        # Add paragraph to result
        if para_comments:
            # Sort comments by number for display
            para_comments.sort(key=lambda x: x[0])
            comment_list = '\n'.join(f'{num}. {text}' for num, text in para_comments)
            result_paragraphs.append(modified_paragraph + '\n\nComments:\n' + comment_list)
        else:
            result_paragraphs.append(modified_paragraph)
        
        # Update character offset (paragraph + double newline)
        char_offset = para_end + 2
    
    return '\n\n'.join(result_paragraphs)


def _format_comments_only(text: str, comments: List[Comment], ranges: List[CommentRange], show_authors: str) -> str:
    """Extract only comments with text context."""
    # Create comment lookup map
    comment_map = {c.id: c for c in comments}
    
    # Determine if we should show authors
    should_show_authors = _should_show_authors(show_authors, comments)
    
    # Sort ranges by start position
    sorted_ranges = sorted(ranges, key=lambda r: r.start_pos)
    
    comment_lines = []
    for range_obj in sorted_ranges:
        comment = comment_map.get(range_obj.comment_id)
        if not comment:
            continue
            
        if range_obj.start_pos == range_obj.end_pos:
            # Point comment
            comment_lines.append(f'[Position {range_obj.start_pos}]: {_format_comment_text(comment, should_show_authors)}')
        else:
            # Range comment - extract the commented text
            commented_text = text[range_obj.start_pos:range_obj.end_pos]
            comment_lines.append(f'"{commented_text}": {_format_comment_text(comment, should_show_authors)}')
    
    return '\n'.join(comment_lines)


def _format_comment_text(comment: Comment, show_author: bool) -> str:
    """Format comment text without brackets (for end-paragraph and comments-only modes)."""
    if show_author and comment.author:
        return f'{comment.author}: {comment.text}'
    else:
        return comment.text