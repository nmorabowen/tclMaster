from __future__ import annotations

from typing import TYPE_CHECKING, List
from pathlib import Path

if TYPE_CHECKING:
    from ..core.core import tclMaster
    from ..utilities.utilities import utilities
    
import re
import shutil

class TclPreprocessor:
    def __init__(self, model: tclMaster):
        self.model = model
        
    def _read_lines(self, file_path: Path) -> List[str]:
        """Helper to read all lines from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _write_lines(self, file_path: Path, lines: List[str]) -> None:
        """Helper to write lines back to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    def backup_file(self, filename: str) -> None:
        """
        Creates a .bak copy of a tcl file before modifying it.
        Useful for debugging if the regex destroys the file.
        """
        # Use utilities to get the full path
        target_file = self.model.utilities.verify_tcl_file(filename)
        backup_path = target_file.with_suffix('.tcl.bak')
        shutil.copy2(target_file, backup_path)

    def inject_line(self, filename: str, content: str, after_pattern: str) -> bool:
            """
            Injects a line of code immediately AFTER a specific regex pattern is found.
            
            Args:
                filename: Name of the tcl file.
                content: The string to insert (auto-adds \n if missing).
                after_pattern: Regex string to find the insertion point.
                
            Returns:
                bool: True if injection happened, False if pattern not found.
            """
            target_file = self.model.utilities.verify_tcl_file(filename)
            lines = self._read_lines(target_file)
            
            pattern = re.compile(after_pattern)
            new_lines = []
            injected = False

            # Ensure content ends with newline
            if not content.endswith('\n'):
                content += '\n'

            for line in lines:
                new_lines.append(line)
                # If we haven't injected yet, check the pattern
                if not injected and pattern.search(line):
                    new_lines.append(content)
                    injected = True
            
            if injected:
                self._write_lines(target_file, new_lines)
                
            return injected

        def replace_variable_value(self, filename: str, var_name: str, new_value: str | float) -> bool:
            """
            Updates the value of a TCL variable.
            Assumes standard TCL syntax: set varName value
            
            Args:
                filename: Name of the tcl file.
                var_name: The variable name (e.g., "dt").
                new_value: The new value.
            """
            target_file = self.model.utilities.verify_tcl_file(filename)
            lines = self._read_lines(target_file)

            # Regex: 
            # ^\s* -> Start of line, optional spaces
            # set\s+ -> literal "set" followed by spaces
            # {var_name}\s+ -> the variable name followed by spaces
            # (.*) -> Capture the old value (everything else)
            pattern = re.compile(rf"^\s*set\s+{re.escape(var_name)}\s+(.*)")
            
            modified = False
            new_lines = []

            for line in lines:
                if pattern.match(line):
                    # Construct the new line preserving indentation is tricky, 
                    # so we stick to a clean standard format.
                    new_lines.append(f"set {var_name} {new_value}\n")
                    modified = True
                else:
                    new_lines.append(line)

            if modified:
                self._write_lines(target_file, new_lines)

            return modified

        def comment_out_block(self, filename: str, start_pattern: str, end_pattern: str) -> int:
            """
            Comments out a block of code between two patterns using #.
            Returns the number of lines commented out.
            """
            target_file = self.model.utilities.verify_tcl_file(filename)
            lines = self._read_lines(target_file)
            
            start_re = re.compile(start_pattern)
            end_re = re.compile(end_pattern)
            
            inside_block = False
            modified_count = 0
            new_lines = []

            for line in lines:
                # Check if block starts
                if not inside_block and start_re.search(line):
                    inside_block = True
                
                if inside_block:
                    # Add # if not already commented
                    if not line.strip().startswith("#"):
                        new_lines.append("# " + line)
                        modified_count += 1
                    else:
                        new_lines.append(line)
                    
                    # Check if block ends (check AFTER commenting current line)
                    if end_re.search(line):
                        inside_block = False
                else:
                    new_lines.append(line)

            if modified_count > 0:
                self._write_lines(target_file, new_lines)
                
            return modified_count
        
    def replace_string_content(self, filename: str, old_string: str, new_string: str) -> int:
            """
            Replaces all occurrences of an old string with a new string in the file content.
            
            It is case-sensitive and uses re.escape() to treat special characters 
            (like file paths with / and .) literally.
            
            Args:
                filename (str): Name of the tcl file (e.g., "setup.tcl").
                old_string (str): The exact string content to search for.
                new_string (str): The replacement string.
                
            Returns:
                int: The total number of replacements made across the entire file.
            """
            target_file = self.model.utilities.verify_tcl_file(filename)
            lines = self._read_lines(target_file)
            
            # 1. Escape the old_string so that path characters (/, .) are treated literally
            search_pattern = re.escape(old_string)
            
            total_replacements = 0
            new_lines = []
            
            for line in lines:
                # 2. Use re.subn to replace all occurrences in the line and count them
                new_line, count = re.subn(search_pattern, new_string, line)
                new_lines.append(new_line)
                total_replacements += count
                
            # 3. Write back only if changes were made
            if total_replacements > 0:
                self._write_lines(target_file, new_lines)
            
            return total_replacements