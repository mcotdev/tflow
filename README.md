# T-Flow Format

A human-readable file format for Machine Translation Post-Editing (MTPE) workflows.

## Quick Start

```bash
# T-Flow to JSONL
python3 tflow_convert.py t2j -i input.tflow -o output.jsonl

# JSONL to T-Flow
python3 tflow_convert.py j2t -i input.jsonl -o output.tflow

# Markdown to T-Flow (for preparing source documents)
python3 tflow_convert.py md2t -i document.md -o output.tflow
```

## Format Overview

T-Flow uses single-character markers at the start of each line:

| Marker | Purpose              |
|--------|----------------------|
| `@`    | Metadata (id, etc.)  |
| `<`    | Source text          |
| `~`    | Machine translation  |
| `>`    | Target (post-edited) |
| `#`    | Comments             |

### Example

```tflow
@ id: 0001
< Hello, world!
~ Hej, verden!
> Hej, verden!
# Simple greeting.

@ id: 0002
< First paragraph.
<
< Second paragraph.
~ Første afsnit.
~
~ Andet afsnit.
> Første afsnit.
>
> Andet afsnit.
# Multi-paragraph example.
```

### Key Rules

- **Segments** are separated by blank lines
- **Paragraphs** within a segment use marker-only lines (e.g., `<` alone)
- **UTF-8** encoding required
- Each segment needs at least one source line (`<`)

## JSONL Format

Each segment becomes a JSON object with these fields:

```json
{
  "id": "0001",
  "meta": ["id: 0001"],
  "source": "Hello.",
  "source_paragraphs": ["Hello."],
  "mt": "Hej.",
  "mt_paragraphs": ["Hej."],
  "target": "Hej.",
  "target_paragraphs": ["Hej."],
  "comments": ["Simple greeting."]
}
```

## Running Tests

```bash
python3 run_conformance_tests.py
```

## Specification

See [SPECS.md](SPECS.md) for the complete format specification.

## License

Creative Commons Attribution 4.0 International (CC BY 4.0)
