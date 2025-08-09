# docx-comments-to-text

Extract reviewer comments from `.docx` files and insert them inline with the text they reference, creating a plain text output that keeps feedback in context.

## Installation

### From PyPI (recommended)
```bash
pip install docx-comments-to-text
```

### From source
```bash
# Clone the repository
git clone https://github.com/platelminto/docx-comments-to-text
cd docx-comments-to-text

# Install in development mode
uv sync --dev
# or: pip install -e .
```

## Usage

### Command Line Interface

```bash
# Basic usage - output to stdout
docx-comments-to-text document.docx

# Save to file
docx-comments-to-text document.docx -o output.txt

# Control author display
docx-comments-to-text document.docx --authors never    # Hide authors
docx-comments-to-text document.docx --authors always   # Always show authors
docx-comments-to-text document.docx --authors auto     # Show authors when multiple exist (default)

# Control comment placement
docx-comments-to-text document.docx --placement inline         # Inline with text (default)
docx-comments-to-text document.docx --placement end-paragraph  # At end of each paragraph
docx-comments-to-text document.docx --placement comments-only  # Comments only with context
```

### Development Usage

If working from source:
```bash
# Run with uv
uv run docx-comments-to-text document.docx

# Or use module syntax
uv run python -m docx_comments_to_text.cli document.docx
```

### Example Output

#### Inline placement (default)
```
Original text with [reviewer feedback] [COMMENT: "This needs clarification"] continues here.
More content [needs examples] [COMMENT John: "Consider adding examples"] and final text.
```

#### End-paragraph placement
```
Original text with reviewer feedback[1] continues here.
More content needs examples[2] and final text.

Comments:
1. This needs clarification
2. John: Consider adding examples
```

#### Comments-only placement
```
"reviewer feedback": This needs clarification
"needs examples": John: Consider adding examples
```

## Features

- Accurate comment positioning and text preservation
- Handles overlapping comments and multiple comment types  
- Configurable author display
- Multiple comment placement styles (inline, end-of-paragraph, comments-only)

## Technical Details

### DOCX Structure
- DOCX files are ZIP archives containing XML files
- `word/document.xml` - main document content
- `word/comments.xml` - comment definitions
- Comment ranges marked with `<w:commentRangeStart>` and `<w:commentRangeEnd>`

### Comment Insertion Strategy
1. Parse document XML to extract text and track character positions
2. Map comment ranges to their start/end positions in the text
3. Sort comments by position for safe insertion (reverse order)
4. Wrap commented text in brackets: `[commented text]`
5. Insert comment content after bracketed text: `[COMMENT: "feedback"]`

## Dependencies

- `python-docx` - DOCX file handling
- `lxml` - XML parsing
- `click` - Command line interface
