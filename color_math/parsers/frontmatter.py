"""YAML frontmatter and tag parser for detecting note domain properties and quantum metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from typing import Any

QUANTUM_TERM_REGEX = re.compile(r"\b(quantum|qm|physics|quantum[-_]mechanics)\b", re.IGNORECASE)
IN_BODY_TAG_REGEX = re.compile(r"(?:^|\s)#(quantum|physics|qm|quantum[-_]mechanics)\b", re.IGNORECASE)


@dataclass
class NoteFieldDetection:
    is_quantum: bool = False
    field: str | None = None
    overrides: dict[str, Any] = dc_field(default_factory=dict)
    theme: str | None = None


def parse_frontmatter_text(content: str) -> dict[str, Any]:
    """Lightweight YAML frontmatter parser for markdown documents."""
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---", content)
    if not match:
        return {}

    lines = match.group(1).splitlines()
    result: dict[str, Any] = {}
    current_parent: str | None = None
    parent_obj: dict[str, Any] = {}

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        is_indented = bool(re.match(r"^\s{2,}|\t", raw_line))
        line = stripped

        # Inline dict e.g. `color-math: { field: quantum }`
        inline_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*\{([^}]*)\}", line)
        if inline_match:
            parent_key = inline_match.group(1)
            inner_pairs = inline_match.group(2).split(",")
            sub_obj: dict[str, Any] = {}
            for pair in inner_pairs:
                parts = pair.split(":", 1)
                if len(parts) == 2:
                    sub_obj[parts[0].strip()] = _parse_yaml_value(parts[1].strip())
            result[parent_key] = sub_obj
            current_parent = None
            continue

        # Parent key without value e.g. `color-math:` or `tags:`
        section_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*$", line)
        if not is_indented and section_match:
            current_parent = section_match.group(1)
            parent_obj = {}
            result[current_parent] = parent_obj
            continue

        # List item e.g. `- item`
        if is_indented and line.startswith("- "):
            item_value = _parse_yaml_value(line[2:].strip())
            if current_parent:
                if not isinstance(result.get(current_parent), list):
                    result[current_parent] = []
                result[current_parent].append(item_value)
            continue

        # Key-value pair
        kv_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if kv_match:
            key = kv_match.group(1)
            val = _parse_yaml_value(kv_match.group(2).strip())
            if is_indented and current_parent:
                parent_obj[key] = val
            else:
                current_parent = None
                result[key] = val

    return result


def _parse_yaml_value(val_str: str) -> Any:
    if not val_str:
        return ""
    if val_str.startswith("[") and val_str.endswith("]"):
        items = val_str[1:-1].split(",")
        return [item.strip().strip("'\"") for item in items if item.strip()]
    if val_str.lower() == "true":
        return True
    if val_str.lower() == "false":
        return False
    if val_str.lower() == "null":
        return None
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        pass
    return val_str.strip("'\"")


def _matches_quantum_term(value: Any) -> bool:
    if isinstance(value, str):
        return bool(QUANTUM_TERM_REGEX.search(value))
    if isinstance(value, list):
        return any(isinstance(item, str) and QUANTUM_TERM_REGEX.search(item) for item in value)
    return False


def detect_note_field(content: str) -> NoteFieldDetection:
    """Inspects markdown note frontmatter and tags to detect quantum domain."""
    frontmatter = parse_frontmatter_text(content)
    overrides: dict[str, Any] = {}
    is_quantum = False
    theme: str | None = None

    # 1. Check explicit color-math block
    color_math_config = frontmatter.get("color-math")
    if isinstance(color_math_config, dict):
        if _matches_quantum_term(color_math_config.get("field")):
            is_quantum = True
        if color_math_config.get("energy-operator") is True or color_math_config.get("energy_operator") is True:
            is_quantum = True
        if isinstance(color_math_config.get("theme"), str):
            theme = color_math_config["theme"]
        if isinstance(color_math_config.get("rainbow-delimiters"), bool):
            overrides["rainbow_delimiters"] = color_math_config["rainbow-delimiters"]
        if isinstance(color_math_config.get("variable-dataflow"), bool):
            overrides["variable_data_flow"] = color_math_config["variable-dataflow"]

    # Flat properties
    if _matches_quantum_term(frontmatter.get("color-math-field")):
        is_quantum = True
    if frontmatter.get("color-math-energy-operator") is True:
        is_quantum = True
    if isinstance(frontmatter.get("color-math-theme"), str):
        theme = frontmatter["color-math-theme"]

    # 2. Check standard note properties: field, subject, topic, discipline, category
    target_keys = ("field", "subject", "topic", "discipline", "category")
    for key in target_keys:
        if _matches_quantum_term(frontmatter.get(key)):
            is_quantum = True
            break

    # 3. Check tags in frontmatter
    if not is_quantum and "tags" in frontmatter:
        if _matches_quantum_term(frontmatter["tags"]):
            is_quantum = True

    # 4. Check in-body tags
    if not is_quantum and IN_BODY_TAG_REGEX.search(content):
        is_quantum = True

    if is_quantum:
        overrides["color_quantum_operators"] = True
        overrides["field"] = "quantum"

    return NoteFieldDetection(
        is_quantum=is_quantum,
        field="quantum" if is_quantum else None,
        overrides=overrides,
        theme=theme,
    )
