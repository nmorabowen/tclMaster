from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

# Keep this for Type Hinting (Intellisense)
if TYPE_CHECKING:
    from ..core.core import tclMaster

def batch_comment_out_block(
    root_paths: Path | list[Path], 
    filename: str, 
    start_pattern: str, 
    end_pattern: str
) -> None:
    """
    Recursively finds all target_files inside the given root path(s) and comments out 
    blocks of code based on start/end regex patterns.
    
    Args:
        root_paths: A single Path object OR a list of Path objects to search.
        filename: The specific file name to look for (e.g., "analysis_steps.tcl").
        start_pattern: Regex string matching the start of the block.
        end_pattern: Regex string matching the end of the block.
    """
    
    # Import here to avoid circular dependency errors
    from ..core.core import tclMaster 
    # --------------------------------------------------------------------

    # 1. Normalize input: Ensure we always work with a list
    if isinstance(root_paths, Path):
        search_targets = [root_paths]
    else:
        search_targets = root_paths

    total_modified_lines_global = 0

    # 2. Iterate over every root path provided
    for current_root in search_targets:
        
        print(f"--- Starting Batch Comment-Out in: {current_root} ---")
        
        # rglob recursively searches for the specific filename in all subfolders
        files_found = list(current_root.rglob(filename))
        
        if not files_found:
            print(f"No files named '{filename}' found in {current_root.name}.")
            continue # Skip to the next root path

        print(f"Found {len(files_found)} models to process in {current_root.name}.\n")
        
        current_root_modifications = 0

        for file_path in files_found:
            # The 'model' folder is the parent of the file we found
            model_dir = file_path.parent
            
            try:
                # Instantiate your class for this specific folder
                model = tclMaster(model_path=model_dir)
                
                # Run the comment block operation
                lines_changed = model.tcl_preprocessor.comment_out_block(
                    filename=filename,
                    start_pattern=start_pattern,
                    end_pattern=end_pattern
                )
                
                if lines_changed > 0:
                    print(f"[Updated] {model_dir.name}: {lines_changed} line(s) commented out")
                    current_root_modifications += lines_changed
                else:
                    print(f"[Skipped] {model_dir.name}: Pattern not found or already commented.")
                    
            except Exception as e:
                print(f"[Error] {model_dir.name}: {e}")
        
        total_modified_lines_global += current_root_modifications
        print(f"--- Finished {current_root.name}. Lines modified: {current_root_modifications} ---\n")

    print(f"=== GLOBAL COMPLETE. Total lines commented out: {total_modified_lines_global} ===")