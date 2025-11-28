#!/usr/bin/env python3
"""
T-Flow <-> JSONL / Markdown converter.

T-Flow is a human-readable format for Machine Translation Post-Editing (MTPE).
See SPECS.md for the full specification.

Usage:
    tflow_convert.py t2j -i input.tflow -o output.jsonl   # T-Flow to JSONL
    tflow_convert.py j2t -i input.jsonl -o output.tflow   # JSONL to T-Flow  
    tflow_convert.py md2t -i input.md -o output.tflow     # Markdown to T-Flow
"""
import argparse
import json
import sys
from typing import Any, Dict, Iterator, List, TextIO

MARKERS = {"@", "<", "~", ">", "#"}


def _new_raw_segment() -> Dict[str, Any]:
    """Create a new empty raw segment structure for parsing."""
    return {
        "meta": [],
        "source_paragraphs": [],
        "mt_paragraphs": [],
        "target_paragraphs": [],
        "comments": [],
    }


def _append_to_role_paragraphs(seg: Dict[str, Any], role: str, text: str) -> None:
    """Append text to the appropriate paragraph list for a role (source/mt/target)."""
    key = f"{role}_paragraphs"
    paras: List[Any] = seg[key]
    if not paras:
        paras.append([])
    if text == "":
        # Empty marker line = paragraph break
        if paras and paras[-1]:
            paras.append([])
    else:
        paras[-1].append(text)


def _normalize_raw_segment(seg: Dict[str, Any]) -> Dict[str, Any]:
    """Convert raw parsed segment to normalized output format with scalar and array fields."""
    obj: Dict[str, Any] = {}
    meta = seg.get("meta") or []
    if meta:
        obj["meta"] = meta
        for m in meta:
            if m.lower().startswith("id:"):
                obj["id"] = m.split(":", 1)[1].strip()
                break

    def finalize_role(role: str, field: str) -> None:
        paras = seg.get(f"{role}_paragraphs") or []
        # Remove trailing empty paragraph if present
        if paras and not paras[-1]:
            paras = paras[:-1]
        out_paras: List[str] = []
        for p in paras:
            if p:
                out_paras.append("\n".join(p))
        if out_paras:
            obj[field] = "\n\n".join(out_paras)
            obj[f"{field}_paragraphs"] = out_paras

    finalize_role("source", "source")
    finalize_role("mt", "mt")
    finalize_role("target", "target")

    if seg.get("comments"):
        obj["comments"] = seg["comments"]
    return obj


def _has_content(seg: Dict[str, Any]) -> bool:
    """Check if a raw segment has any meaningful content."""
    return bool(
        seg.get("meta")
        or any(seg.get("source_paragraphs", []))
        or any(seg.get("mt_paragraphs", []))
        or any(seg.get("target_paragraphs", []))
        or seg.get("comments")
    )


def iter_tflow_segments(fp: TextIO) -> Iterator[Dict[str, Any]]:
    """
    Parse T-Flow format from a file-like object, yielding normalized segments.
    
    Implements streaming parser that holds at most one segment in memory.
    """
    current: Dict[str, Any] | None = None

    for raw in fp:
        line = raw.rstrip("\r\n")
        if not line.strip():
            # Blank line = segment separator
            if current is not None and _has_content(current):
                yield _normalize_raw_segment(current)
            current = None
            continue
        
        if line[0] not in MARKERS:
            raise ValueError(f"Invalid T-Flow line (no marker): {line!r}")
        
        marker = line[0]
        text = line[1:].lstrip(" ")[:len(line)-1] if len(line) > 1 else ""
        # Preserve exact content after marker+optional space
        text = line[2:] if len(line) > 1 and line[1] == " " else line[1:]
        
        if current is None:
            current = _new_raw_segment()
        
        if marker == "@":
            current["meta"].append(text)
        elif marker == "<":
            _append_to_role_paragraphs(current, "source", text)
        elif marker == "~":
            _append_to_role_paragraphs(current, "mt", text)
        elif marker == ">":
            _append_to_role_paragraphs(current, "target", text)
        elif marker == "#":
            current["comments"].append(text)

    # Yield final segment if file doesn't end with blank line
    if current is not None and _has_content(current):
        yield _normalize_raw_segment(current)


def write_jsonl_stream(segments: Iterator[Dict[str, Any]], fp: TextIO) -> None:
    """Write segments to JSONL format (one JSON object per line)."""
    for seg in segments:
        fp.write(json.dumps(seg, ensure_ascii=False))
        fp.write("\n")


def _write_role_lines(obj: Dict[str, Any], marker: str, field: str, fp: TextIO) -> None:
    """Write source/mt/target lines for a segment."""
    paras_key = f"{field}_paragraphs"
    paras = obj.get(paras_key)
    text_value = obj.get(field)
    
    if isinstance(paras, list) and paras:
        paragraphs = [
            p.split("\n") if isinstance(p, str) else [str(x) for x in p]
            for p in paras
        ]
    elif isinstance(text_value, str):
        paragraphs = [p.split("\n") for p in text_value.split("\n\n")]
    else:
        return
    
    for i, para in enumerate(paragraphs):
        if i > 0:
            fp.write(f"{marker}\n")  # Paragraph separator
        for ln in para:
            fp.write(f"{marker} {ln}\n" if ln else f"{marker}\n")


def write_tflow_segment(obj: Dict[str, Any], fp: TextIO) -> None:
    """Write a single segment in T-Flow format."""
    # Write ID first if present
    id_value = obj.get("id")
    if id_value is not None:
        fp.write(f"@ id: {id_value}\n")
    
    # Write other metadata (skip id: if already written)
    for m in obj.get("meta") or []:
        if isinstance(m, str) and not (id_value and m.lower().startswith("id:")):
            fp.write(f"@ {m}\n")

    _write_role_lines(obj, "<", "source", fp)
    _write_role_lines(obj, "~", "mt", fp)
    _write_role_lines(obj, ">", "target", fp)

    for c in obj.get("comments") or []:
        if isinstance(c, str):
            fp.write(f"# {c}\n")


def jsonl_to_tflow_stream(fp_in: TextIO, fp_out: TextIO) -> None:
    """Convert JSONL input to T-Flow output."""
    first = True
    for raw in fp_in:
        line = raw.strip()
        if not line:
            continue
        obj = json.loads(line)
        if not first:
            fp_out.write("\n")  # Segment separator
        first = False
        write_tflow_segment(obj, fp_out)


def markdown_to_tflow_stream(fp_in: TextIO, fp_out: TextIO) -> None:
    """
    Convert Markdown to T-Flow format.
    
    Each block of text (separated by blank lines) becomes a segment.
    Fenced code blocks are kept as single segments.
    """
    blocks: List[List[str]] = []
    current: List[str] = []
    in_code = False
    
    for raw in fp_in:
        line = raw.rstrip("\r\n")
        stripped = line.strip()
        
        # Handle fenced code blocks
        if stripped.startswith("```"):
            in_code = not in_code
            current.append(line)
            continue
        
        if in_code:
            current.append(line)
            continue
        
        # Blank line = block separator (outside code)
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue
        
        current.append(line)
    
    if current:
        blocks.append(current)
    
    # Write blocks as T-Flow segments
    for idx, block in enumerate(blocks, start=1):
        if idx > 1:
            fp_out.write("\n")
        fp_out.write(f"@ id: {idx:04d}\n")
        for ln in block:
            fp_out.write(f"< {ln}\n" if ln else "<\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="T-Flow <-> JSONL / Markdown converter.",
        epilog="See SPECS.md for format details.",
    )
    parser.add_argument("mode", choices=["t2j", "j2t", "md2t"],
                        help="t2j: T-Flow→JSONL, j2t: JSONL→T-Flow, md2t: Markdown→T-Flow")
    parser.add_argument("-i", "--input", default="-", help="Input file (default: stdin)")
    parser.add_argument("-o", "--output", default="-", help="Output file (default: stdout)")
    args = parser.parse_args()

    fp_in = sys.stdin if args.input == "-" else open(args.input, "r", encoding="utf-8")
    fp_out = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")

    try:
        if args.mode == "t2j":
            write_jsonl_stream(iter_tflow_segments(fp_in), fp_out)
        elif args.mode == "j2t":
            jsonl_to_tflow_stream(fp_in, fp_out)
        elif args.mode == "md2t":
            markdown_to_tflow_stream(fp_in, fp_out)
    finally:
        if fp_in is not sys.stdin:
            fp_in.close()
        if fp_out is not sys.stdout:
            fp_out.close()


if __name__ == "__main__":
    main()
