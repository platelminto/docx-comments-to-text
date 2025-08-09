from click.testing import CliRunner
from pathlib import Path
import tempfile
import os
from cli import main

class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()
        self.test_docx = Path(__file__).parent / "docs" / "simple_comment.docx"
    
    def test_cli_stdout_output(self):
        """Test CLI outputs to stdout when no output file specified"""
        result = self.runner.invoke(main, [str(self.test_docx)])
        
        assert result.exit_code == 0
        assert "[COMMENT:" in result.output
        assert "Hello [world] [COMMENT:" in result.output
    
    def test_cli_file_output(self):
        """Test CLI writes to file when output specified"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            output_path = tmp.name
        
        try:
            result = self.runner.invoke(main, [str(self.test_docx), '-o', output_path])
            
            assert result.exit_code == 0
            assert f"Output written to: {output_path}" in result.output
            
            # Verify file contents
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "[COMMENT:" in content
            assert "Hello [world] [COMMENT:" in content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_cli_authors_option(self):
        """Test CLI authors option"""
        result = self.runner.invoke(main, [str(self.test_docx), '--authors', 'never'])
        
        assert result.exit_code == 0
        # Should not contain author names when set to 'never'
        assert "Author:" not in result.output or "[COMMENT:" in result.output
    
    def test_cli_nonexistent_file(self):
        """Test CLI handles nonexistent input file"""
        result = self.runner.invoke(main, ['nonexistent.docx'])
        
        assert result.exit_code != 0
        assert "Error:" in result.output
    
    def test_cli_help(self):
        """Test CLI shows help"""
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert "Extract comments from DOCX files" in result.output
        assert "--authors" in result.output
        assert "--output" in result.output