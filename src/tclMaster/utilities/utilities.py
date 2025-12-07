"""Utility helpers for inspecting and managing TCL model assets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Set
from pathlib import Path
import re

if TYPE_CHECKING:
    from ..core.core import tclMaster
    
class utilities:
    """Collection of convenience helpers bound to a single `tclMaster` model."""

    def __init__(self, model: tclMaster) -> None:
        """Bind the helpers to a `tclMaster` instance.

        Args:
            model: The owning facade that exposes the model directory and peers.
        """
        self.model = model

    @property
    def model_path(self) -> Path:
        """Return the filesystem path of the bound model."""
        return self.model.model_path

    def list_tcl_files(self) -> list[Path]:
        """Return every `.tcl` file located directly inside the model path."""
        return list(self.model_path.glob("*.tcl"))
    
    def list_mpco_files(self) -> Set[str]:
        """Extract the distinct recorder names from `.mpco` and `.mpco.cdata` files."""
        mpco_files = (
            list(self.model_path.glob("*.mpco")) +
            list(self.model_path.glob("*.mpco.cdata"))
        )

        recorder_names: Set[str] = set()
        
        # Matches "name" in "name.part-0.mpco"
        pattern = re.compile(r"^(?P<recorder>.+?)\.part-\d+\.mpco")

        for f in mpco_files:
            match = pattern.match(f.name)
            if match:
                recorder_names.add(match.group("recorder"))

        return recorder_names
    
    def get_number_of_partitions_from_mpco(self) -> int:
        """Infer the partition count encoded in `.mpco` file names."""
        mpco_files = list(self.model_path.glob("*.mpco")) + \
                     list(self.model_path.glob("*.mpco.cdata"))

        partition_ids: Set[int] = set()

        # OPTIMIZATION: Compile once, use many times
        pattern = re.compile(r"\.part-(\d+)\.mpco")

        for f in mpco_files:
            # We use search because the pattern is in the middle of the string
            m = pattern.search(f.name)
            if m:
                partition_ids.add(int(m.group(1)))

        if not partition_ids:
            # If files exist but no ".part-XX" pattern, it's a serial run (1 partition)
            return 1 if mpco_files else 0

        return len(partition_ids)
    
    def list_path_files(self) -> None:
        """Print every file and folder located in the model path."""
        for f in self.model_path.iterdir():
            print(f.name)
            
    def copy_folder_structure(self, source: Path, destination: Path) -> None:
        """Mirror the directory layout from `source` into `destination` minus files."""
        for item in source.iterdir():
            dest_item = destination / item.name
            if item.is_dir():
                dest_item.mkdir(parents=True, exist_ok=True)
                self.copy_folder_structure(item, dest_item)
                
    def verify_tcl_file(self, filename: str) -> Path:
        """Ensure a `.tcl` file exists within the model directory.

        Args:
            filename: Base name or filename with optional `.tcl` suffix.

        Returns:
            Full `Path` pointing to the verified file.

        Raises:
            FileNotFoundError: Raised when the resolved path does not exist.
        """
        if not filename.endswith('.tcl'):
            filename += '.tcl'

        target_file = self.model_path / filename

        if not target_file.is_file():
            raise FileNotFoundError(
                f"Critical Error: The required file '{filename}' was not found in "
                f"the model directory: '{self.model_path}'"
            )

        return target_file