from __future__ import annotations

import difflib
import re
from typing import List, Tuple


# Paragraph separator: one or more blank lines (possibly with spaces/tabs in them)
_PARAGRAPH_SEP_RE = re.compile(r"\n\s*\n+")


def _tokenize_with_whitespace(text: str) -> List[str]:
    """
    Split text into a sequence of tokens preserving all whitespace.

    Each token is either:
      - a run of non-whitespace characters (a word/punctuation), or
      - a run of whitespace characters (spaces, newlines, tabs, etc.).
    """
    return re.findall(r"\S+|\s+", text)


def _split_marked_spans_by_paragraphs(
    text: str,
    marker: Tuple[str, str],
) -> str:
    """
    Ensure that spans marked with 'marker' do not cross paragraph boundaries.

    If we have something like:

        [-First paragraph text.\n\nSecond paragraph text.-]

    this becomes:

        [-First paragraph text.-]\n\n[-Second paragraph text.-]
    """
    start, end = marker
    result_parts: List[str] = []
    i: int = 0
    n: int = len(text)

    while True:
        # Find next start marker
        s = text.find(start, i)
        if s == -1:
            # No more markers
            result_parts.append(text[i:])
            break

        # Add text before the marker unchanged
        result_parts.append(text[i:s])

        # Find matching end marker
        e = text.find(end, s + len(start))
        if e == -1:
            # Unmatched start marker; append the rest and stop
            result_parts.append(text[s:])
            break

        # Inner content between markers
        inner = text[s + len(start) : e]

        # Split inner content into paragraph chunks and separators
        pieces = _PARAGRAPH_SEP_RE.split(inner)
        for piece in pieces:
            if not piece:
                continue
            if _PARAGRAPH_SEP_RE.fullmatch(piece):
                # Paragraph separator: emit as-is, outside of markers
                result_parts.append(piece)
            else:
                # Non-separator text: wrap again in markers
                result_parts.append(f"{start}{piece}{end}")

        # Continue after the end marker
        i = e + len(end)

    return "".join(result_parts)


def diff_texts_inline(
    original: str,
    modified: str,
    deletion_marker: Tuple[str, str] = ("[-", "-]"),
    insertion_marker: Tuple[str, str] = ("[+", "+]"),
) -> str:
    """
    Return a printable, word-level diff string between two multi-paragraph texts.

    Deletions are marked as:  deletion_marker[0] + deleted_text + deletion_marker[1]
    Insertions are marked as: insertion_marker[0] + inserted_text + insertion_marker[1]

    Properties
    ----------
    - Works well for very large paragraphs with many sentences.
    - Changes are highlighted at word granularity.
    - Marked spans never cross paragraph boundaries (blank lines).

    Parameters
    ----------
    original : str
        The original text.
    modified : str
        The modified text.
    deletion_marker : tuple[str, str], optional
        Prefix and suffix used to mark deleted spans.
    insertion_marker : tuple[str, str], optional
        Prefix and suffix used to mark inserted spans.

    Returns
    -------
    str
        A single diff string with inline markers, preserving original
        whitespace (including paragraph breaks).
    """
    orig_tokens: List[str] = _tokenize_with_whitespace(original)
    mod_tokens: List[str] = _tokenize_with_whitespace(modified)

    sm = difflib.SequenceMatcher(a=orig_tokens, b=mod_tokens)
    parts: List[str] = []

    del_start, del_end = deletion_marker
    ins_start, ins_end = insertion_marker

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            parts.extend(orig_tokens[i1:i2])
        elif tag == "delete":
            deleted = "".join(orig_tokens[i1:i2])
            if deleted:
                parts.append(f"{del_start}{deleted}{del_end}")
        elif tag == "insert":
            inserted = "".join(mod_tokens[j1:j2])
            if inserted:
                parts.append(f"{ins_start}{inserted}{ins_end}")
        elif tag == "replace":
            deleted = "".join(orig_tokens[i1:i2])
            inserted = "".join(mod_tokens[j1:j2])
            if deleted:
                parts.append(f"{del_start}{deleted}{del_end}")
            if inserted:
                parts.append(f"{ins_start}{inserted}{ins_end}")

    diff_text = "".join(parts)

    # Post-process so that no marker span crosses a paragraph boundary.
    diff_text = _split_marked_spans_by_paragraphs(diff_text, deletion_marker)
    diff_text = _split_marked_spans_by_paragraphs(diff_text, insertion_marker)

    return diff_text


if __name__ == "__main__":
    v1 = (
        "This is a very long paragraph that contains several sentences. "
        "This sentence stays unchanged. "
        "Some of the sentences will change slightly.\n\n"
        "Here is another paragraph that stays mostly the same.\n\n"
        "This paragraph stays entirely unchanged.\n\n"
        "This sentence will add something new.\n\n"
        "This one will be deleted."
    )

    v2 = (
        "This is a very long paragraph that contains many sentences. "
        "This sentence stays unchanged. "
        "Some of these sentences will change slightly.\n\n"
        "Here is another paragraph that stays almost the same.\n\n"
        "This paragraph stays entirely unchanged.\n\n"
        "This sentence will add something new..."
    )

    print(diff_texts_inline(v1, v2))