import click
import sys
from pathlib import Path
from docx_parser import DocxParser
from text_formatter import format_text_with_comments

@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', 'output_file', type=click.Path(path_type=Path), 
              help='Output file path. If not specified, prints to stdout.')
@click.option('--authors', type=click.Choice(['never', 'always', 'auto']), default='auto',
              help='How to display comment authors (default: auto)')
def main(input_file: Path, output_file: Path, authors: str):
    """Extract comments from DOCX files and insert them inline with the text."""
    
    try:
        # Parse the DOCX file
        parser = DocxParser(str(input_file))
        text, comments, ranges = parser.extract_text_and_comments()
        
        # Format text with comments
        formatted_text = format_text_with_comments(text, comments, ranges, show_authors=authors)
        
        # Output the result
        if output_file:
            output_file.write_text(formatted_text, encoding='utf-8')
            click.echo(f"Output written to: {output_file}")
        else:
            click.echo(formatted_text)
            
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error processing file: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
