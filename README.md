# docx-to-text-with-comments

Extract reviewer comments from `.docx` files and insert them inline with the text they reference, creating a plain text output that keeps feedback in context.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd docx-comments-to-text

# Install dependencies
uv sync
# or: pip install python-docx lxml click
```

## Usage

### Command Line Interface

```bash
# Basic usage - output to stdout
python main.py document.docx

# Save to file
python main.py document.docx -o output.txt

# Control author display
python main.py document.docx --authors never    # Hide authors
python main.py document.docx --authors always   # Always show authors
python main.py document.docx --authors auto     # Show authors when multiple exist (default)
```

### Example Output

Input document with comments becomes:
```
Original text with [reviewer feedback] [COMMENT: "This needs clarification"] continues here.
More content [needs examples] [COMMENT John: "Consider adding examples"] and final text.
```

## Features

- Accurate comment positioning and text preservation
- Handles overlapping comments and multiple comment types  
- Configurable author display

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