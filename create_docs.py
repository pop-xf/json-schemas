#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json, textwrap, re
from typing import Any
from pathlib import Path

SCHEMA_PATH = "popxf-1.0.json"
OUTPUT_MD = "README.md"

def is_scalar(x: Any) -> bool:
    """Return True if x is a 'scalar' for our purposes."""
    return isinstance(x, (int, float, str)) or x is None or isinstance(x, bool)

def all_scalars(arr):
    return all(is_scalar(el) for el in arr)

def format_json_doc(obj, indent=2, _level=0):
    """
    Pretty-print `obj` as JSON for documentation:
    - objects get multiline with indentation
    - arrays of scalars go on one line: [1, 2, 3]
    - arrays of non-scalars expand one item per line
    Returns a string.
    """
    space = " " * (indent * _level)
    space_inner = " " * (indent * (_level + 1))

    # 1. Scalars
    if is_scalar(obj):
        return json.dumps(obj)

    # 2. Arrays
    if isinstance(obj, list):
        if len(obj) == 0:
            return "[]"

        if all_scalars(obj):
            # single-line
            inner = ", ".join(json.dumps(el) for el in obj)
            return "[" + inner + "]"
        else:
            # multi-line: one item per line
            pieces = []
            for el in obj:
                pieces.append(space_inner + format_json_doc(el, indent, _level + 1))
            return "[\n" + ",\n".join(pieces) + "\n" + space + "]"

    # 3. Objects / dicts
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        pieces = []
        for i, (k, v) in enumerate(obj.items()):
            key_repr = json.dumps(k)
            val_repr = format_json_doc(v, indent, _level + 1)
            pieces.append(f"{space_inner}{key_repr}: {val_repr}")
        return "{\n" + ",\n".join(pieces) + "\n" + space + "}"

    # 4. Fallback (shouldn't really happen for valid JSON types)
    return json.dumps(obj)

def get_type_string(spec):
    if spec is True:   # “accept anything”
        return "any"
    if spec is False:  # “accept nothing”
        return "forbidden"
    if not isinstance(spec, dict):
        return None

    if "type" in spec:
        t = spec["type"]
    elif "oneOf" in spec:
        t = [alt.get("type") for alt in spec["oneOf"] if isinstance(alt, dict) and "type" in alt]
        t = t[0] if len(set(t)) == 1 else ", ".join(filter(None, t))
    elif "anyOf" in spec:
        t = [alt.get("type") for alt in spec["anyOf"] if isinstance(alt, dict) and "type" in alt]
        t = t[0] if len(set(t)) == 1 else ", ".join(filter(None, t))
    else:
        t = None

    if t == "array":
        items = spec.get("items", {})
        if isinstance(items, dict) and "type" in items:
            it = items["type"]
            t = f"array of {', '.join(it) if isinstance(it, list) else it}"
    return t or None

def format_examples_for_markdown(examples):
    """
    Takes the 'examples' array from the schema property
    and turns it into fenced ```json blocks.
    """
    blocks = []
    for ex in examples:
        # extract description if present
        if isinstance(ex, dict) and "description" in ex:
            desc = ex.pop("description")
            blocks.append(f"\n{desc}")
        pretty = format_json_doc(ex, indent=2).strip("{}").strip("\n")
        blocks.append(f"```json\n{pretty}\n```")
    return "\n\n".join(blocks)

def _render_schema_bullets(spec, name=None, indent=""):
    lines = []

    # handle boolean / non-dict as before...
    if spec is True:
        if name is not None: lines.append(f"{indent}- `{name}` (*type: any*)")
        return lines
    if spec is False:
        if name is not None: lines.append(f"{indent}- `{name}` (*forbidden*)")
        return lines
    if not isinstance(spec, dict):
        return lines

    t = spec.get("type")

    # --- Arrays: render items first; do NOT early-return on anyOf here
    if t == "array":
        items = spec.get("items", {})
        if name is not None:
            lines.append(f"{indent}- `{name}` (*type: {get_type_string(spec) or 'array'}*)")
            indent += "  "
        if items not in (None, {}):
            lines.extend(_render_schema_bullets(items, name=None, indent=indent))
        return lines

    # --- Objects: render properties / maps first; do NOT early-return on anyOf here
    if t == "object" and ("properties" in spec or "additionalProperties" in spec):
        if name is not None:
            lines.append(f"{indent}- `{name}` (*type: object*)")
            indent += "  "

        # explicit properties
        if "properties" in spec:
            props = spec["properties"]
            req = set(spec.get("required", []))
            for child, child_spec in props.items():
                child_req  = "required" if child in req else "optional"
                child_type = get_type_string(child_spec) or "any"
                desc = (child_spec.get("description") or "").strip()
                header = f"{indent}- **`{child}` ({child_req}, *type: {child_type}*)**"
                if desc:
                    header += f": {desc}"
                lines.append(header)

                # recurse into child
                lines.extend(_render_schema_bullets(child_spec, name=None, indent=indent + "  "))

                # show child examples
                child_examples = child_spec.get("examples")
                if child_examples:
                    lines.append("")
                    lines.append("  Example:" if len(child_examples) == 1 else "  Examples:")
                    pretty = format_examples_for_markdown(child_examples)
                    indented = "\n".join("  " + ln if ln else "" for ln in pretty.splitlines())
                    lines.append(indented)

        # map-like additionalProperties (incl. anyOf)
        if "additionalProperties" in spec:
            ap = spec["additionalProperties"]
            if isinstance(ap, dict) and ("anyOf" in ap or "oneOf" in ap):
                alts = ap.get("anyOf") or ap.get("oneOf") or []
                for alt in alts:
                    alt_desc = (alt.get("description") or "").strip()
                    alt_type = get_type_string(alt) or "any"
                    if alt_desc:
                        lines.append(f"{indent}- {alt_desc or f'Value of type *{alt_type}*'}")
                        lines.extend(_render_schema_bullets(alt, name=None, indent=indent + "  "))
        return lines

    # --- If we reach here and there ARE combinators, expand them now (fallback)
    for comb_key in ("anyOf", "oneOf"):
        alts = spec.get(comb_key)
        if isinstance(alts, list):
            for alt in alts:
                lines.extend(_render_schema_bullets(alt, name=name, indent=indent))
            return lines

    # --- Leaf
    if name is not None and t:
        lines.append(f"{indent}- `{name}` (*type: {get_type_string(spec)}*)")
    return lines

def emit_section(md_lines, prop_name, spec, is_required):
    """
    Render a section for a field:
      - header with required/type
      - description
      - bullets for substructure (objects, arrays of objects)
      - examples for the field itself
    """
    desc       = (spec.get("description") or "").strip()
    examples   = spec.get("examples", [])
    field_type = get_type_string(spec) or "any"
    req_str    = "required" if is_required else "optional"

    # Heading
    md_lines.append(f"### `{prop_name}` ({req_str}, *type: {field_type}*)")
    md_lines.append("")

    # Description
    if desc:
        md_lines.append(desc)
        md_lines.append("")

    # Substructure bullets:
    #  - object: document properties
    #  - array of objects: document items' properties
    sub_bullets = _render_schema_bullets(spec, name=None, indent="")
    if sub_bullets:
        md_lines.extend(sub_bullets)
        md_lines.append("")

    # Examples for the field itself
    if examples:
        md_lines.append("Example:" if len(examples) == 1 else "Examples:")
        md_lines.append("")
        md_lines.append(format_examples_for_markdown(examples))
        md_lines.append("")

def walk_properties(md_lines, schema_section):
    """
    schema_section: e.g. schema["properties"]["metadata"]
    section_name: e.g. "metadata"
    """
    md_lines.append(f"## {schema_section.get('title', '').strip()}")
    md_lines.append(schema_section.get("description", "").strip())
    md_lines.append("")  # spacer

    props_obj = schema_section.get("properties", {})
    required_fields = set(schema_section.get("required", []))

    for name, spec in props_obj.items():
        is_required = name in required_fields
        emit_section(md_lines, name, spec, is_required)

def write_markdown(schema, out_path):
    md_lines = []
    md_lines.append(f"# {schema.get('title', '').strip()}")
    md_lines.append(schema.get("description", "").strip())
    md_lines.append("")  # spacer

    metadata_section = schema["properties"]["$schema"]
    walk_properties(md_lines, metadata_section)

    metadata_section = schema["properties"]["metadata"]
    walk_properties(md_lines, metadata_section)

    data_section = schema["properties"]["data"]
    walk_properties(md_lines, data_section)

    Path(out_path).write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {out_path}")

def to_latex_with_pypandoc(md_path, tex_path):
    try:
        import pypandoc
    except ImportError:
        raise SystemExit("pypandoc not installed. `pip install pypandoc pandoc-minted`")

    # Markdown → LaTeX (minted)
    tex = pypandoc.convert_file(
        md_path, to="latex",
        extra_args=[
            "--filter=pandoc-minted",
            "--natbib",
        ]
    )
    # Turn \citep and \citet into plain \cite
    tex = re.sub(r'\s*\\cite[p|t]?', r'~\\cite', tex)
    with open(tex_path, 'w') as f:
        f.write(tex)
    print(f"Wrote {tex_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", default=SCHEMA_PATH)
    parser.add_argument("--md", default=OUTPUT_MD)
    parser.add_argument("--tex", help="Write LaTeX fragment to this path (uses pypandoc).")
    args = parser.parse_args()

    with open(args.schema, "r", encoding="utf-8") as f:
        schema = json.load(f)

    write_markdown(schema, args.md)

    if args.tex:
        tex_path = args.tex or Path(args.md).with_suffix(".tex")
        to_latex_with_pypandoc(args.md, str(tex_path))

if __name__ == "__main__":
    main()
