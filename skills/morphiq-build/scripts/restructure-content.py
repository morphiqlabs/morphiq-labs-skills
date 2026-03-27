#!/usr/bin/env python3
"""restructure-content.py — Fix heading hierarchy, split paragraphs, reorder sections.

Usage: echo '{"content": "..."}' | python3 restructure-content.py
Output: JSON with restructured content and changes made
"""

import json
import re
import sys


def fix_heading_hierarchy(content: str) -> tuple:
    """Fix heading level violations (skips, multiple H1s)."""
    lines = content.split("\n")
    changes = []
    h1_seen = False
    expected_min_level = 1

    for i, line in enumerate(lines):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not match:
            continue

        level = len(match.group(1))
        text = match.group(2)

        # Fix multiple H1s
        if level == 1:
            if h1_seen:
                lines[i] = f"## {text}"
                changes.append(f"Line {i+1}: Demoted duplicate H1 to H2: '{text}'")
            else:
                h1_seen = True
                expected_min_level = 2

    return "\n".join(lines), changes


def split_long_paragraphs(content: str, max_words: int = 75) -> tuple:
    """Split paragraphs exceeding the word limit."""
    lines = content.split("\n\n")
    result = []
    changes = []

    for block in lines:
        # Skip headings, lists, code blocks, blockquotes
        if re.match(r'^[#\-*>`]|\d+\.', block.strip()):
            result.append(block)
            continue

        # Skip short blocks
        words = block.split()
        if len(words) <= max_words:
            result.append(block)
            continue

        # Split at sentence boundaries near the midpoint
        sentences = re.split(r'(?<=[.!?])\s+', block)
        if len(sentences) <= 1:
            result.append(block)
            continue

        # Find split point near max_words
        current_words = 0
        split_idx = 0
        for j, sentence in enumerate(sentences):
            current_words += len(sentence.split())
            if current_words >= max_words * 0.6:
                split_idx = j + 1
                break

        if split_idx > 0 and split_idx < len(sentences):
            part1 = " ".join(sentences[:split_idx])
            part2 = " ".join(sentences[split_idx:])
            result.append(part1)
            result.append(part2)
            changes.append(f"Split {len(words)}-word paragraph into two")
        else:
            result.append(block)

    return "\n\n".join(result), changes


def ensure_answer_first(content: str) -> tuple:
    """Check that sections start with direct answers, not preamble."""
    changes = []
    sections = re.split(r'(^#{2,3}\s+.+$)', content, flags=re.MULTILINE)

    # Analysis only — actual rewriting requires Claude
    for i, section in enumerate(sections):
        if re.match(r'^#{2,3}\s+', section):
            # Check the next section (content after heading)
            if i + 1 < len(sections):
                body = sections[i + 1].strip()
                first_para = body.split("\n\n")[0] if body else ""

                # Flag preamble patterns
                preamble_signals = [
                    "in this section", "let's explore", "we will discuss",
                    "before we", "it's important to note", "first, let's",
                ]
                if any(signal in first_para.lower() for signal in preamble_signals):
                    heading_text = section.strip()
                    changes.append(f"Section '{heading_text}' starts with preamble — needs direct answer opening")

    return content, changes


def add_missing_structure(content: str) -> tuple:
    """Identify missing structural elements."""
    changes = []

    # Check for TL;DR
    if "tl;dr" not in content.lower() and not re.search(r'^>\s+', content, re.MULTILINE):
        changes.append("Missing TL;DR or blockquote summary — add after H1")

    # Check for FAQ
    headings = re.findall(r'^#{2,3}\s+(.+)$', content, re.MULTILINE)
    has_faq = any("faq" in h.lower() or "frequently" in h.lower() for h in headings)
    if not has_faq:
        changes.append("Missing FAQ section — add before sources/end")

    # Check for sources section
    has_sources = any("source" in h.lower() or "reference" in h.lower() for h in headings)
    if not has_sources:
        changes.append("Missing Sources section — add at end")

    return content, changes


def restructure(content: str) -> dict:
    """Run all restructuring passes."""
    all_changes = []

    content, heading_changes = fix_heading_hierarchy(content)
    all_changes.extend(heading_changes)

    content, split_changes = split_long_paragraphs(content)
    all_changes.extend(split_changes)

    content, answer_changes = ensure_answer_first(content)
    all_changes.extend(answer_changes)

    content, structure_changes = add_missing_structure(content)
    all_changes.extend(structure_changes)

    return {
        "content": content,
        "changes_made": all_changes,
        "total_changes": len(all_changes),
        "word_count": len(content.split()),
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    content = data.get("content", "")
    result = restructure(content)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
