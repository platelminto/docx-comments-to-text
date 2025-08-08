from typing import List
from docx_parser import Comment, CommentRange

def format_text_with_comments(text: str, comments: List[Comment], ranges: List[CommentRange], show_authors: str = "auto") -> str:
    """
    Format text by inserting comments inline with their referenced text.
    
    Range comments: [commented text] [COMMENT: "feedback"]
    Point comments: [COMMENT: "feedback"] (inserted at position)
    
    Args:
        text: Original document text
        comments: List of Comment objects
        ranges: List of CommentRange objects mapping comments to text positions
        show_authors: "never", "always", or "auto" (default: "auto")
                     - "never": never show authors
                     - "always": always show authors as "Author: text"
                     - "auto": show authors only when multiple authors exist
        
    Returns:
        Formatted text with comments inserted inline
    """
    if not ranges:
        return text
    
    # Create comment lookup map
    comment_map = {c.id: c for c in comments}
    
    # Determine if we should show authors
    should_show_authors = _should_show_authors(show_authors, comments)
    
    # Group ranges by position to handle multiple comments on same text
    from collections import defaultdict
    position_groups = defaultdict(list)
    
    for range_obj in ranges:
        key = (range_obj.start_pos, range_obj.end_pos)
        position_groups[key].append(range_obj)
    
    # Sort position groups by start position in reverse order for safe insertion
    sorted_positions = sorted(position_groups.keys(), key=lambda pos: pos[0], reverse=True)
    
    result = text
    
    for start_pos, end_pos in sorted_positions:
        range_group = position_groups[(start_pos, end_pos)]
        
        # Collect all comments for this position
        group_comments = []
        for range_obj in range_group:
            comment = comment_map.get(range_obj.comment_id)
            if comment:
                group_comments.append(comment)
        
        if not group_comments:
            continue
        
        if start_pos == end_pos:
            # Point comments - insert all at position
            comment_texts = ' '.join(_format_comment(comment, should_show_authors) for comment in group_comments)
            result = (result[:start_pos] + 
                     comment_texts + 
                     result[start_pos:])
        else:
            # Range comments - wrap text once and add all comments after
            comment_texts = ' '.join(_format_comment(comment, should_show_authors) for comment in group_comments)
            
            # First insert all comments after the range end
            result = (result[:end_pos] + 
                     f' {comment_texts}' + 
                     result[end_pos:])
            
            # Then wrap the range text in brackets (only once)
            result = (result[:start_pos] + 
                     '[' + result[start_pos:end_pos] + ']' + 
                     result[end_pos:])
    
    return result


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