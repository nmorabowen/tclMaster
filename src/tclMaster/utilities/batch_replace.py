from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

# Keep this for Type Hinting (Intellisense)
if TYPE_CHECKING:
    from ..core.core import tclMaster

def batch_replace(
    root_paths: Path | list[Path], 
    target_filename: str, 
    old_str: str, 
    new_str: str
) -> None:
    """
    Recursively finds all target_files inside the given root path(s) and performs string replacement.
    
    Args:
        root_paths: A single Path object OR a list of Path objects to search.
        target_filename: The specific file name to look for (e.g., "analysis_steps.tcl").
        old_str: The string to replace.
        new_str: The replacement string.
    """
    
    # Import here to avoid circular dependency errors
    from ..core.core import tclMaster 
    # --------------------------------------------------------------------

    # 1. Normalize input: Ensure we always work with a list
    if isinstance(root_paths, Path):
        search_targets = [root_paths]
    else:
        search_targets = root_paths

    total_replacements_global = 0

    # 2. Iterate over every root path provided
    for current_root in search_targets:
        
        print(f"--- Starting Batch Replacement in: {current_root} ---")
        
        # rglob recursively searches for the specific filename in all subfolders
        files_found = list(current_root.rglob(target_filename))
        
        if not files_found:
            print(f"No files named '{target_filename}' found in {current_root.name}.")
            continue # Skip to the next root path

        print(f"Found {len(files_found)} models to process in {current_root.name}.\n")
        
        current_root_replacements = 0

        for file_path in files_found:
            # The 'model' folder is the parent of the file we found
            model_dir = file_path.parent
            
            try:
                # Instantiate your class for this specific folder
                model = tclMaster(model_path=model_dir)
                
                # Run the replacement
                count = model.tcl_preprocessor.replace_string_content(
                    filename=target_filename,
                    old_string=old_str,
                    new_string=new_str
                )
                
                if count > 0:
                    print(f"[Updated] {model_dir.name}: {count} replacement(s)")
                    current_root_replacements += count
                else:
                    print(f"[Skipped] {model_dir.name}: String not found.")
                    
            except Exception as e:
                print(f"[Error] {model_dir.name}: {e}")
        
        total_replacements_global += current_root_replacements
        print(f"--- Finished {current_root.name}. Replacements: {current_root_replacements} ---\n")

    print(f"=== GLOBAL COMPLETE. Total replacements made: {total_replacements_global} ===")