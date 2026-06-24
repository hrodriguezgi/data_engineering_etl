#!/usr/bin/env python3
"""
Convert Jupyter-style Python files (with # %% cells) to .ipynb notebooks.

Usage:
    python py_to_notebook.py <module_dir>

Converts all 0X_*.py files in module_dir to notebooks/0X_*.ipynb
"""

import json
import re
import sys
from pathlib import Path


def parse_python_cells(content: str) -> list[dict]:
    """Parse Python file with # %% cells into notebook cells."""
    cells = []
    lines = content.split("\n")
    current_cell = []
    cell_type = "code"
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for cell marker
        if line.startswith("# %% [markdown]"):
            # Save previous cell
            if current_cell:
                cells.append({
                    "cell_type": cell_type,
                    "content": "\n".join(current_cell),
                })
                current_cell = []

            # Extract markdown content
            markdown_lines = []
            i += 1
            while i < len(lines):
                if lines[i].startswith("# %%") or lines[i].startswith("# %% [markdown]"):
                    i -= 1
                    break
                if lines[i].startswith("# "):
                    # Remove "# " prefix and unescape markdown
                    markdown_lines.append(lines[i][2:])
                else:
                    break
                i += 1

            if markdown_lines:
                cells.append({
                    "cell_type": "markdown",
                    "content": "\n".join(markdown_lines),
                })
            cell_type = "code"

        elif line.startswith("# %%"):
            # Code cell marker
            if current_cell:
                cells.append({
                    "cell_type": cell_type,
                    "content": "\n".join(current_cell),
                })
                current_cell = []
            cell_type = "code"

        else:
            current_cell.append(line)

        i += 1

    # Save last cell
    if current_cell:
        cells.append({
            "cell_type": cell_type,
            "content": "\n".join(current_cell),
        })

    return cells


def cells_to_notebook(cells: list[dict]) -> dict:
    """Convert parsed cells to notebook JSON format."""
    notebook_cells = []

    for cell in cells:
        content = cell["content"].strip()
        if not content:
            continue

        if cell["cell_type"] == "markdown":
            notebook_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [line + "\n" for line in content.split("\n")[:-1]] + [content.split("\n")[-1]],
            })
        else:
            notebook_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in content.split("\n")[:-1]] + [content.split("\n")[-1]],
            })

    notebook = {
        "cells": notebook_cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }

    return notebook


def convert_module(module_dir: Path):
    """Convert all lesson files in a module to notebooks."""
    # Create notebooks directory
    notebooks_dir = module_dir.parent / "notebooks"
    notebooks_dir.mkdir(exist_ok=True)

    # Find and convert all lesson files
    lesson_files = sorted(module_dir.glob("0[0-9]_*.py"))

    for py_file in lesson_files:
        print(f"Converting {py_file.name}...", end=" ")

        # Read Python file
        content = py_file.read_text()

        # Parse cells
        cells = parse_python_cells(content)

        # Create notebook
        notebook = cells_to_notebook(cells)

        # Write notebook
        nb_file = notebooks_dir / py_file.name.replace(".py", ".ipynb")
        nb_file.write_text(json.dumps(notebook, indent=2))

        print(f"✓ → {nb_file.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python py_to_notebook.py <module_dir>")
        sys.exit(1)

    module_dir = Path(sys.argv[1])
    if not module_dir.is_dir():
        print(f"Error: {module_dir} is not a directory")
        sys.exit(1)

    convert_module(module_dir)
    print("\nDone!")
