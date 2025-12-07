from __future__ import annotations

from typing import TYPE_CHECKING, List
from pathlib import Path
import re
import shutil

if TYPE_CHECKING:
    from ..core.core import tclMaster

class TclPreprocessor:
    """
    Handles the programmatic modification of Tcl input files for OpenSees/STKO.
    
    This class acts as a 'surgeon' for text files, allowing the user to inject code,
    update variables, and fix paths without manually opening the files. It relies on
    the parent `tclMaster` object to locate files safely.

    Attributes:
        model (tclMaster): Reference to the main model object managing the directory.
    """

    def __init__(self, model: tclMaster):
        """
        Initializes the preprocessor with a reference to the model master.

        Args:
            model (tclMaster): The main application object containing the 'utilities' module.
        """
        self.model = model
        
    def _read_lines(self, file_path: Path) -> List[str]:
        """
        Internal helper to read all lines from a file safely.

        Args:
            file_path (Path): The full path object to the file.

        Returns:
            List[str]: A list of strings, where each element is a line from the file.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _write_lines(self, file_path: Path, lines: List[str]) -> None:
        """
        Internal helper to write a list of lines back to a file.

        Args:
            file_path (Path): The full path object to the destination file.
            lines (List[str]): The content to write.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    def backup_file(self, filename: str) -> None:
        """
        Creates a backup copy (.bak) of a specified Tcl file.

        This is useful before performing destructive regex operations. The backup
        is created in the same directory as the original file.

        Args:
            filename (str): The name of the Tcl file (e.g., "analysis_steps.tcl").

        Raises:
            FileNotFoundError: If the source file does not exist.
        """
        # Use utilities to get the full path
        target_file = self.model.utilities.verify_tcl_file(filename)
        backup_path = target_file.with_suffix('.tcl.bak')
        shutil.copy2(target_file, backup_path)

    def inject_line(self, filename: str, content: str, after_pattern: str) -> bool:
        """
        Injects a line of code immediately AFTER the first occurrence of a regex pattern.

        Args:
            filename (str): Name of the Tcl file.
            content (str): The string code to insert. A newline is automatically appended
                           if missing.
            after_pattern (str): The regex pattern used to locate the insertion point.

        Returns:
            bool: True if the pattern was found and the line injected; False otherwise.

        Raises:
            FileNotFoundError: If the Tcl file is not found.
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
        Updates the value of a Tcl variable defined with the 'set' command.

        This method specifically looks for lines matching: `set var_name value`.

        Args:
            filename (str): Name of the Tcl file.
            var_name (str): The variable name to search for (e.g., "dt", "pi").
            new_value (str | float): The new value to assign to the variable.

        Returns:
            bool: True if the variable was found and updated; False otherwise.
        """
        target_file = self.model.utilities.verify_tcl_file(filename)
        lines = self._read_lines(target_file)

        # Regex explanation: 
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
        Comments out a block of code between (and including) two regex patterns.

        Lines are prepended with '# '.

        Args:
            filename (str): Name of the Tcl file.
            start_pattern (str): Regex marking the beginning of the block to comment.
            end_pattern (str): Regex marking the end of the block.

        Returns:
            int: The total number of lines that were modified (commented out).
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
        Global search-and-replace for a specific string within a file.

        This is useful for updating file paths, inclusion directories, or specific
        text strings that are not simple variable definitions. It automatically escapes
        special characters in `old_string` to ensure literal matching.

        Args:
            filename (str): Name of the Tcl file (e.g., "setup.tcl").
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