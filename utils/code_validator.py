import ast
import py_compile
import tempfile
import os
from typing import Tuple, List

class CodeValidator:
    """Advanced code validator with syntax checking and error detection"""
    
    @staticmethod
    def validate_python_code(code: str) -> Tuple[bool, List[str]]:
        """
        Validate Python code for syntax errors
        Returns: (is_valid, errors_list)
        """
        errors = []
        
        try:
            # Try to parse the code with AST
            ast.parse(code)
            
            # Try to compile the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                py_compile.compile(temp_file, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"Compilation Error: {str(e)}")
            finally:
                os.unlink(temp_file)
            
            # Additional checks
            errors.extend(CodeValidator._check_dangerous_code(code))
            
        except SyntaxError as e:
            errors.append(f"Syntax Error at line {e.lineno}: {e.msg}")
            if e.text:
                errors.append(f"Code: {e.text.strip()}")
                errors.append(f"      {' ' * (e.offset - 1)}^")
        except Exception as e:
            errors.append(f"Unexpected Error: {str(e)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_javascript_code(code: str) -> Tuple[bool, List[str]]:
        """
        Basic JavaScript validation
        Returns: (is_valid, errors_list)
        """
        errors = []
        
        # Basic syntax checks for JavaScript
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(code):
            if char in brackets.keys():
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    errors.append(f"Bracket mismatch at position {i}")
        
        if stack:
            errors.append("Unclosed brackets found")
        
        # Check for common syntax patterns
        if 'function' in code and '()' not in code:
            errors.append("Warning: Function declaration might be incomplete")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _check_dangerous_code(code: str) -> List[str]:
        """Check for potentially dangerous code patterns"""
        warnings = []
        
        dangerous_imports = ['os.system', 'subprocess', 'eval', 'exec', '__import__']
        
        for dangerous in dangerous_imports:
            if dangerous in code:
                warnings.append(f"⚠️ Warning: Found potentially dangerous code: '{dangerous}'")
        
        return warnings
    
    @staticmethod
    def get_detailed_error_report(code: str, file_type: str) -> str:
        """Generate a beautiful error report"""
        if file_type == 'python':
            is_valid, errors = CodeValidator.validate_python_code(code)
        elif file_type == 'javascript':
            is_valid, errors = CodeValidator.validate_javascript_code(code)
        else:
            return "❌ Unsupported file type"
        
        if is_valid:
            return "✅ **Code Validation Successful!**\n\nNo syntax errors found. Your code is ready to run!"
        else:
            report = "❌ **Code Validation Failed!**\n\n"
            report += "**Errors Found:**\n\n"
            for i, error in enumerate(errors, 1):
                report += f"{i}. {error}\n"
            report += "\n📝 **Please fix these errors and try again.**"
            return report
