"""
Supreme Hosting Bot - Robust Syntax Checker
Uses AST module for Python syntax validation
"""

import ast
import py_compile
import tempfile
import os
import traceback
from typing import Tuple, Optional


class SyntaxChecker:
    """
    Multi-layer syntax validation for Python files.
    Layer 1: AST parsing
    Layer 2: py_compile
    """

    @staticmethod
    def check_python_syntax(code: str, filename: str = "<uploaded>") -> Tuple[bool, Optional[str], int]:
        """
        Check Python code for syntax errors.
        
        Returns:
            (is_valid, error_message, error_line)
        """
        # Layer 1: AST parsing
        try:
            ast.parse(code, filename=filename)
        except SyntaxError as e:
            line_no = e.lineno or 0
            offset = e.offset or 0
            error_text = e.msg or str(e)
            
            # Build detailed error message
            lines = code.splitlines()
            context = ""
            if line_no > 0 and line_no <= len(lines):
                start = max(0, line_no - 3)
                end = min(len(lines), line_no + 2)
                for i in range(start, end):
                    marker = " >> " if i == line_no - 1 else "    "
                    context += f"{marker}{i + 1:4d} | {lines[i]}\n"
                if offset > 0:
                    context += f"         {' ' * (offset - 1)}^\n"
            
            error_msg = (
                f"SyntaxError: {error_text}\n"
                f"Line: {line_no}, Column: {offset}\n\n"
                f"Context:\n{context}"
            )
            return False, error_msg, line_no
            
        except Exception as e:
            return False, f"Parsing Error: {str(e)}", 0

        # Layer 2: py_compile check
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.py', delete=False, encoding='utf-8'
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            
            try:
                py_compile.compile(tmp_path, doraise=True)
            except py_compile.PyCompileError as e:
                error_msg = str(e)
                # Try to extract line number
                line_no = 0
                try:
                    if hasattr(e, 'exc_value') and hasattr(e.exc_value, 'lineno'):
                        line_no = e.exc_value.lineno or 0
                except:
                    pass
                return False, f"CompileError:\n{error_msg}", line_no
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            # If py_compile fails but AST passed, we still accept
            pass

        return True, None, 0

    @staticmethod
    def check_file(file_path: str) -> Tuple[bool, Optional[str], int]:
        """Check a Python file on disk for syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                code = f.read()
            return SyntaxChecker.check_python_syntax(code, filename=os.path.basename(file_path))
        except Exception as e:
            return False, f"Failed to read file: {str(e)}", 0

    @staticmethod
    def get_imports(code: str) -> list:
        """Extract all import module names from code."""
        try:
            tree = ast.parse(code)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
            return list(imports)
        except:
            return []
