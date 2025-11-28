# T-Flow Format Specification

## Abstract

T-Flow is a human-readable file format designed for **Machine Translation Post-Editing (MTPE)** workflows. It provides a structured way to represent translation segments with source text, machine translation output, and post-edited target text, while maintaining readability and editability for human translators.

## Status

This document specifies version 1.0 of the T-Flow format. This is a **DRAFT** specification and may be updated based on implementation experience and community feedback.

## Table of Contents

1. [Introduction](#1-introduction)  
   1.1. [Purpose and Scope](#11-purpose-and-scope)  
   1.2. [Conventions Used in This Document](#12-conventions-used-in-this-document)

2. [Terminology](#2-terminology)

3. [Data Model](#3-data-model)  
   3.1. [Translation Segment](#31-translation-segment)  
   3.2. [Paragraph Structure](#32-paragraph-structure)  
   3.3. [Metadata](#33-metadata)

4. [Concrete Syntax](#4-concrete-syntax)  
   4.1. [Marker Characters](#41-marker-characters)  
   4.2. [Line Format](#42-line-format)  
   4.3. [Segment Separation](#43-segment-separation)  
   4.4. [Paragraph Separation](#44-paragraph-separation)

5. [Encoding and Decoding](#5-encoding-and-decoding)  
   5.1. [Character Encoding](#51-character-encoding)  
   5.2. [Line Endings](#52-line-endings)  
   5.3. [Normalization Rules](#53-normalization-rules)

6. [JSONL Representation](#6-jsonl-representation)  
   6.1. [JSONL Format](#61-jsonl-format)  
   6.2. [Field Mapping](#62-field-mapping)  
   6.3. [Paragraph Representation](#63-paragraph-representation)

7. [Markdown Conversion](#7-markdown-conversion)  
   7.1. [Markdown to T-Flow](#71-markdown-to-t-flow)  
   7.2. [Code Block Handling](#72-code-block-handling)

8. [Implementation Requirements](#8-implementation-requirements)  
   8.1. [Parser Requirements](#81-parser-requirements)  
   8.2. [Serializer Requirements](#82-serializer-requirements)  
   8.3. [Stream Processing](#83-stream-processing)

9. [Conformance](#9-conformance)  
   9.1. [T-Flow Files](#91-t-flow-files)  
   9.2. [JSONL Files](#92-jsonl-files)  
   9.3. [Implementation Conformance](#93-implementation-conformance)

Appendix A. [Examples](#appendix-a-examples)  
Appendix B. [ABNF Grammar](#appendix-b-abnf-grammar)  
Appendix C. [Implementation Notes](#appendix-c-implementation-notes)  
Appendix D. [Version History](#appendix-d-version-history)  
Appendix E. [Conformance Tests](#appendix-e-conformance-tests)

---

## 1. Introduction

### 1.1. Purpose and Scope

The T-Flow format addresses the need for a human-editable format that can represent the complete MTPE workflow:

- **Source text** in the original language  
- **Machine translation** output  
- **Post-edited target text** after human review  
- **Metadata** and **comments** for translation instructions

This specification defines the T-Flow format syntax, semantics, and the conversion rules to and from JSONL format for machine processing.

### 1.2. Conventions Used in This Document

The key words **"MUST"**, **"MUST NOT"**, **"REQUIRED"**, **"SHALL"**, **"SHALL NOT"**, **"SHOULD"**, **"SHOULD NOT"**, **"RECOMMENDED"**, **"MAY"**, and **"OPTIONAL"** in this document are to be interpreted as described in RFC 2119.

---

## 2. Terminology

- **Translation Segment**: A unit of translatable content, typically corresponding to a sentence, paragraph, or UI string.  
- **Source Text**: The original text to be translated.  
- **Machine Translation (MT)**: The output from automated translation systems.  
- **Target Text**: The final translated text after human post-editing.  
- **Paragraph**: A block of text within a segment, separated by explicit paragraph breaks in the T-Flow syntax.  
- **Metadata**: Additional information about a segment (e.g., ID, context, instructions).  
- **Comments**: Human-readable notes for translators.

---

## 3. Data Model

### 3.1. Translation Segment

A translation segment MUST contain the following components:

- **Metadata** (optional): Key-value style data providing segment context  
- **Source Paragraphs** (required): One or more paragraphs of source text  
- **MT Paragraphs** (optional): One or more paragraphs of machine translation  
- **Target Paragraphs** (optional): One or more paragraphs of post-edited text  
- **Comments** (optional): Translator notes and instructions

### 3.2. Paragraph Structure

In the data model:

- Paragraphs MUST be represented as strings.  
- Multi-paragraph content MUST be represented as an ordered list of paragraph strings.  
- When serialized into a single string field (e.g., `source`, `mt`, `target` in JSONL), implementations MUST:
  - Join lines within a paragraph using a single newline (`
`), and  
  - Join paragraphs using a double newline (`

`) separator.

### 3.3. Metadata

Metadata SHOULD include at minimum a unique identifier for the segment.

Common metadata fields include (informal, not enforced by the syntax):

- `id`: Unique segment identifier  
- `context`: Source file or location context  
- `instructions`: Translation guidelines  
- `status`: Workflow status (e.g., Draft, Approved)

The T-Flow syntax treats metadata lines as opaque strings. Higher-level tools MAY parse key-value pairs as needed.

---

## 4. Concrete Syntax

### 4.1. Marker Characters

The T-Flow format uses marker characters at the beginning of each non-blank line to indicate the type of content:

| Marker | Purpose              | Required |
|--------|----------------------|----------|
| `@`    | Metadata             | Optional |
| `<`    | Source text          | Required |
| `~`    | Machine translation  | Optional |
| `>`    | Target text          | Optional |
| `#`    | Comments             | Optional |

### 4.2. Line Format

Each **non-blank** line in a T-Flow file MUST begin with exactly one of the marker characters, followed by optional whitespace and then the content text.

General form:

```text
@ id: 0001
< This is source text.
~ This is machine translation.
> This is post-edited text.
# This is a comment.
```

Details:

- A marker line MAY have no content after the marker. In that case:
  - For `<`, `~`, `>` lines, this indicates a paragraph break for that role (see §4.4).
  - For `@` and `#`, an empty content part is allowed but has no special semantics.
- Implementations MUST NOT treat any character other than `@`, `<`, `~`, `>`, `#` as a valid marker.

### 4.3. Segment Separation

Segments MUST be separated by one or more **blank lines**.

- A blank line is defined as a line containing only whitespace characters (spaces, tabs) or being completely empty.  
- Implementations MUST treat any sequence of one or more blank lines between non-blank lines as a single segment separator.  
- Blank lines MUST NOT carry content and MUST NOT begin with marker characters.

### 4.4. Paragraph Separation

Paragraph separation applies only to the source (`<`), MT (`~`), and target (`>`) roles.

Within a segment:

- `MARKER text` (e.g., `< Text`) adds a line to the current paragraph for that role.  
- A marker-only line (`<`, `~`, or `>`, with no content text after the marker) marks a paragraph break. The next non-empty marker line of the same type starts a new paragraph.

Example:

```text
< First paragraph line 1
< First paragraph line 2
<
< Second paragraph line 1
```

This decodes to:

- Paragraph 1: `"First paragraph line 1
First paragraph line 2"`  
- Paragraph 2: `"Second paragraph line 1"`

Empty paragraphs that contain no textual lines MUST be ignored in the data model.

Metadata (`@`) and comment (`#`) lines are not structured into paragraphs.

---

## 5. Encoding and Decoding

### 5.1. Character Encoding

T-Flow files MUST be encoded in UTF-8.

Implementations:

- MUST support UTF-8 decoding and encoding.  
- MUST preserve all valid Unicode scalar values, including Nordic letters (æ, ø, å, ä, ö), emoji, and right-to-left scripts.  
- SHOULD NOT use other character encodings.

### 5.2. Line Endings

Implementations MUST support both:

- Unix-style line endings (`
`), and  
- Windows-style line endings (`
`).

When writing T-Flow files, implementations SHOULD use the platform-appropriate line ending.

### 5.3. Normalization Rules

When reading T-Flow files, implementations:

- MUST treat lines containing only whitespace characters as **blank lines** (segment separators).  
- MUST treat any **non-blank** line that does not begin with a valid marker character as a parsing error.  
- SHOULD preserve leading and trailing whitespace on content text after the marker.  
- MUST ignore empty paragraphs (paragraphs with no content lines) in the data model.  
- MUST treat multiple consecutive blank lines between segments as a single segment separator.

---

## 6. JSONL Representation

### 6.1. JSONL Format

JSONL (JSON Lines) format represents each translation segment as a separate JSON object on its own line.

- Each line MUST contain one valid JSON object.  
- All JSONL files MUST be encoded as UTF-8.  
- JSON objects SHOULD NOT span multiple lines.

### 6.2. Field Mapping

The following fields SHOULD be used to map between T-Flow and JSONL:

| T-Flow Component     | JSONL Field             | Type           |
|----------------------|-------------------------|----------------|
| Metadata lines (`@`) | `meta`                  | Array of strings |
| Source text          | `source`                | String         |
| Source paragraphs    | `source_paragraphs`     | Array of strings |
| MT text              | `mt`                    | String         |
| MT paragraphs        | `mt_paragraphs`         | Array of strings |
| Target text          | `target`                | String         |
| Target paragraphs    | `target_paragraphs`     | Array of strings |
| Comment lines (`#`)  | `comments`              | Array of strings |
| ID (from metadata)   | `id`                    | String         |

Conforming encoders MUST correctly populate these fields when the corresponding data exists in the segment. Conforming decoders MUST correctly interpret these fields when present.

### 6.3. Paragraph Representation

For each of `source`, `mt`, and `target`:

- The `*_paragraphs` field MUST represent paragraphs as an array of strings, each string representing one paragraph.  
- The corresponding scalar field (e.g., `source`) MUST contain the concatenation of the same paragraphs using:
  - A single newline (`
`) between lines inside a paragraph, and  
  - A double newline (`

`) between paragraphs.

Implementations MUST preserve this relationship during round-trip conversion between T-Flow and JSONL.

---

## 7. Markdown Conversion

### 7.1. Markdown to T-Flow

When converting from Markdown to T-Flow:

- Each block of text (group of non-blank lines separated by blank lines) MUST become a separate translation segment.  
- Markdown content within a block MUST be preserved as-is in the `<` (source) lines.  
- Each resulting segment MUST be assigned a sequential ID (e.g., `0001`, `0002`, …), encoded in metadata as `@ id: 0001`.  
- The `~` (MT) and `>` (target) roles SHOULD be left empty by the markdown converter, to be filled later by MT systems or human translators.

### 7.2. Code Block Handling

Code blocks in Markdown, fenced with triple backticks (```), MUST be treated as part of a single block:

- The entire fenced code block (including internal blank lines) MUST be contained within a single T-Flow segment.  
- Code blocks MUST NOT be split across multiple segments.  
- The fenced block text MUST be preserved as-is in `<` lines.

---

## 8. Implementation Requirements

### 8.1. Parser Requirements

A conformant T-Flow parser MUST:

- Read files as UTF-8.  
- Normalize both `
` and `
` line endings.  
- Treat lines containing only whitespace as blank lines and segment separators.  
- Validate that every non-blank line begins with one of the marker characters `@`, `<`, `~`, `>`, `#`.  
- Interpret marker-only lines for `<`, `~`, `>` as paragraph breaks.  
- Preserve paragraph structure such that paragraphs and lines can be reconstructed from the syntax.  
- Generate clear error messages when encountering:
  - Non-blank lines without valid markers  
  - Malformed UTF-8 sequences  
  - Invalid JSON (when parsing JSONL, if implemented)

### 8.2. Serializer Requirements

A conformant T-Flow serializer MUST:

- Write files in valid T-Flow syntax as defined in §4.  
- Use UTF-8 encoding.  
- Use appropriate line endings for the platform.  
- Preserve all content from the data model, including:
  - Metadata lines  
  - Paragraph structure  
  - Comments  
- Generate sequential IDs when converting from Markdown, unless IDs are provided by the caller.  
- Preserve special characters (including Nordic letters, emojis, and other Unicode characters) without lossy transformations.

### 8.3. Stream Processing

To support large translation projects (100k+ words and beyond), implementations SHOULD:

- Support streaming / incremental processing, ensuring that at most one segment needs to be held in memory at a time.  
- Avoid loading entire T-Flow or JSONL files into memory when not necessary.  
- Use efficient string handling for paragraph concatenation and splitting.

---

## 9. Conformance

### 9.1. T-Flow Files

A T-Flow file is conformant if:

- It is encoded in UTF-8.  
- Every non-blank line begins with a valid marker character (`@`, `<`, `~`, `>`, `#`).  
- Lines containing only whitespace are treated solely as blank lines and segment separators.  
- It uses blank lines to separate segments.  
- It contains at least one source text line (`<`) in each segment.  

### 9.2. JSONL Files

A JSONL file is conformant if:

- Each line contains a single valid JSON object.  
- The file is encoded in UTF-8.  
- When used with T-Flow, JSON objects correctly represent segments using the fields defined in §6.2.  
- Arrays of paragraphs and their scalar counterparts (e.g., `source_paragraphs` and `source`) are consistent as described in §6.3.

### 9.3. Implementation Conformance

An implementation is conformant if:

- It can read and write conformant T-Flow and JSONL files.  
- It preserves all data during a T-Flow → JSONL → T-Flow round-trip, modulo insignificant differences in whitespace and field ordering in JSON.  
- It handles the complete data model defined in §3.  
- It supports UTF-8 encoding for all inputs and outputs.  
- It implements the normalization rules in §5.3.

---

## Appendix A. Examples

### A.1. Basic T-Flow Example

```tflow
@ id: 0001
< # Welcome
<
< This app helps you track your tasks.
~ # Velkommen
~
~ Denne app hjælper dig med at holde styr på dine opgaver.
> # Velkommen
>
> Denne app hjælper dig med at holde styr på dine opgaver.
# Style: Brug "du"-form på dansk.

@ id: 0002
< Click "Submit" to continue.
~ Klik på "Send" for at fortsætte.
> Klik på "Send" for at fortsætte.
# Kort og direkte.
```

### A.2. Corresponding JSONL Example

```json
{"id": "0001", "meta": ["id: 0001"], "source": "# Welcome\n\nThis app helps you track your tasks.", "source_paragraphs": ["# Welcome", "This app helps you track your tasks."], "mt": "# Velkommen\n\nDenne app hjælper dig med at holde styr på dine opgaver.", "mt_paragraphs": ["# Velkommen", "Denne app hjælper dig med at holde styr på dine opgaver."], "target": "# Velkommen\n\nDenne app hjælper dig med at holde styr på dine opgaver.", "target_paragraphs": ["# Velkommen", "Denne app hjælper dig med at holde styr på dine opgaver."], "comments": ["Style: Brug \"du\"-form på dansk."]}
{"id": "0002", "meta": ["id: 0002"], "source": "Click \"Submit\" to continue.", "source_paragraphs": ["Click \"Submit\" to continue."], "mt": "Klik på \"Send\" for at fortsætte.", "mt_paragraphs": ["Klik på \"Send\" for at fortsætte."], "target": "Klik på \"Send\" for at fortsætte.", "target_paragraphs": ["Klik på \"Send\" for at fortsætte."], "comments": ["Kort og direkte."]}
```

---

## Appendix B. ABNF Grammar

The following ABNF grammar (RFC 5234) describes the high-level structure of T-Flow files. It is an ASCII-based approximation; in a conformant implementation, `TEXTCHAR` MUST represent arbitrary UTF-8 encoded Unicode characters except CR and LF.

```abnf
TFlowFile   = *(BlankLine) [ Segment *(BlankLine Segment) ] *(BlankLine)

Segment     = *MetadataLine 1*SourceLine *MTLine *TargetLine *CommentLine

; Lines

MetadataLine = "@" [SP *TEXTCHAR] CRLF
SourceLine   = "<" [SP *TEXTCHAR] CRLF
MTLine       = "~" [SP *TEXTCHAR] CRLF
TargetLine   = ">" [SP *TEXTCHAR] CRLF
CommentLine  = "#" [SP *TEXTCHAR] CRLF

BlankLine    = *WSP CRLF

; Characters

SP        = %x20
WSP       = SP / HTAB
HTAB      = %x09

; TEXTCHAR is an ASCII stand-in. Real implementations MUST support UTF-8 and
; treat TEXTCHAR as arbitrary Unicode scalar values except CR and LF.
TEXTCHAR  = VCHAR / %x80-FF
VCHAR     = %x21-7E

CRLF      = %x0D %x0A / %x0A
```

Note: This grammar constrains the ordering of lines within a segment for simplicity. Implementations MAY support more flexible ordering (e.g., interleaving comments) as long as the semantic rules in this specification are respected.

---

## Appendix C. Implementation Notes

### C.1. Error Handling

Implementations SHOULD provide clear error messages when encountering:

- Non-blank lines without valid marker characters  
- Malformed UTF-8 sequences  
- Invalid JSON in JSONL files  
- Inconsistent paragraph representations between `*_paragraphs` and scalar `*` fields

### C.2. Performance Considerations

For large translation projects, implementations SHOULD:

- Use stream processing to avoid memory issues  
- Implement efficient string handling for paragraph concatenation and splitting  
- Use generators / iterators when processing large T-Flow or JSONL files

---

## Appendix D. Version History

### Version 1.0 (DRAFT)

- Initial specification  
- Defines T-Flow format syntax and semantics  
- Specifies JSONL conversion rules  
- Defines Markdown conversion behavior  
- Specifies streaming and UTF-8 requirements

---

## Appendix E. Conformance Tests

This appendix describes a minimal set of conformance tests for implementations.

### E.1. Test Fixtures

The reference repository includes the following fixtures:

- `tests/basic.tflow`: A small T-Flow file with two segments.  
- `tests/basic.jsonl`: A JSONL file representing the same segments.

`tests/basic.tflow`:

```tflow
@ id: 0001
< Hello.
~ Hej.
> Hej.
# Simple greeting.

@ id: 0002
< Line one.
<
< Line two.
~ Linie ét.
~
~ Linie to.
> Linie ét.
>
> Linie to.
# Two-paragraph example.
```

`tests/basic.jsonl`:

```json
{"id": "0001", "meta": ["id: 0001"], "source": "Hello.", "source_paragraphs": ["Hello."], "mt": "Hej.", "mt_paragraphs": ["Hej."], "target": "Hej.", "target_paragraphs": ["Hej."], "comments": ["Simple greeting."]}
{"id": "0002", "meta": ["id: 0002"], "source": "Line one.\n\nLine two.", "source_paragraphs": ["Line one.", "Line two."], "mt": "Linie ét.\n\nLinie to.", "mt_paragraphs": ["Linie ét.", "Linie to."], "target": "Linie ét.\n\nLinie to.", "target_paragraphs": ["Linie ét.", "Linie to."], "comments": ["Two-paragraph example."]}
```

### E.2. Round-Trip Test Script

A simple reference script `run_conformance_tests.py` is provided. It:

1. Runs `t2j` (T-Flow → JSONL) on `tests/basic.tflow`.  
2. Compares the resulting JSONL objects with `tests/basic.jsonl`.  
3. Runs `j2t` (JSONL → T-Flow) on `tests/basic.jsonl`.  
4. Runs `t2j` again on the regenerated T-Flow and compares the resulting JSONL with `tests/basic.jsonl`.  

If all comparisons succeed, the implementation passes the basic conformance tests.

Implementations MAY add additional fixtures and tests, but SHOULD at minimum pass this basic round-trip test suite.

---

**Copyright** © 2025 T-Flow Contributors.  
This specification is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
