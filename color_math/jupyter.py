"""Jupyter Server & Notebook 7 integration for color-math.

Provides automated pre-save formatting so that whenever a notebook is saved
in Jupyter Notebook 7 or JupyterLab, all LaTeX formulas in Markdown cells
are automatically colorized.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .config import ColorMathOptions
from .converters.block import convert_text
from .undo import uncolor_text


HOOK_SNIPPET = """
# >>> color-math Jupyter pre-save hook >>>
try:
    from color_math.jupyter import notebook_pre_save_hook
    c.FileContentsManager.pre_save_hook = notebook_pre_save_hook
except ImportError:
    pass
# <<< color-math Jupyter pre-save hook <<<
"""


def notebook_pre_save_hook(
    model: dict[str, Any],
    os_path: str = "",
    contents_manager: Any = None,
    options: ColorMathOptions | None = None,
    **kwargs: Any,
) -> None:
    """Jupyter FileContentsManager pre_save_hook.

    Modifies the notebook model in-place before it is written to disk.
    """
    if model.get("type") != "notebook":
        return

    content = model.get("content")
    if not isinstance(content, dict):
        return

    cells = content.get("cells")
    if not isinstance(cells, list):
        return

    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") != "markdown":
            continue

        source = cell.get("source", "")
        if isinstance(source, str):
            joined = source
        elif isinstance(source, list) and all(isinstance(part, str) for part in source):
            joined = "".join(source)
        else:
            continue

        converted = convert_text(joined, options=options)
        if converted != joined:
            if isinstance(source, str):
                cell["source"] = converted
            else:
                cell["source"] = converted.splitlines(keepends=True) or ([""] if source else [])


def get_jupyter_config_dir() -> Path:
    """Locate the active Jupyter user configuration directory."""
    env_dir = os.environ.get("JUPYTER_CONFIG_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".jupyter"


def install_jupyter_hook(config_dir: Path | str | None = None) -> Path:
    """Install the pre-save hook into the user's Jupyter configuration."""
    target_dir = Path(config_dir) if config_dir else get_jupyter_config_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    # In modern Jupyter (Notebook 7 / JupyterLab 4), jupyter_server_config.py is preferred
    config_file = target_dir / "jupyter_server_config.py"
    if not config_file.exists():
        legacy_file = target_dir / "jupyter_notebook_config.py"
        if legacy_file.exists():
            config_file = legacy_file

    existing_content = config_file.read_text(encoding="utf-8") if config_file.exists() else ""
    if "color_math.jupyter" in existing_content:
        return config_file

    with open(config_file, "a", encoding="utf-8") as f:
        f.write(HOOK_SNIPPET + "\n")

    return config_file
