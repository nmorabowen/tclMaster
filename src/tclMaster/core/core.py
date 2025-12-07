"""Core orchestration layer for tclMaster.

This module exposes the `tclMaster` facade, which wires together helper
utilities and preprocessors that operate on a TCL-based structural model.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..utilities import utilities
from ..utilities import TclPreprocessor


class tclMaster:
    """High-level facade that coordinates utilities for a TCL model workspace."""

    def __init__(
        self,
        model_path: Path,
    ) -> None:
        """Instantiate the controller for a specific model directory.

        Args:
            model_path: Filesystem path to the folder that holds all model
                artifacts (e.g., `.tcl`, `.mpco`).
        """

        self.model_path = model_path
        
        # Create composites classes
        self.utilities = utilities(model=self)
        self.tcl_preprocessor = TclPreprocessor(model=self)
        
        # Get useful info about the model
        self.tcl_files = self.list_tcl_files()
        
    def list_tcl_files(self) -> list[Path]:
        """Return all `.tcl` files in the model directory via the utilities helper."""
        return self.utilities.list_tcl_files()

    def print_model_info(self) -> None:
        """Prints basic information about the model."""
        print(f"Model path: {self.model_path}")
        print(f"Number of .tcl files: {len(self.tcl_files)}")
    
    
