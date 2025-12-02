from __future__ import annotations

import difflib
import re
from typing import List, Optional, Tuple


# Paragraph separator: one or more blank lines (possibly with spaces/tabs).
# The capturing group ensures separators are retained by re.split.
_PARAGRAPH_SEP_RE = re.compile(r"(\n\s*\n+)")


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

    Paragraph boundaries are defined by _PARAGRAPH_SEP_RE.
    """
    start, end = marker
    result_parts: List[str] = []
    i: int = 0

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
        for idx, piece in enumerate(pieces):
            if not piece:
                continue
            if idx % 2 == 1:
                # Paragraph separator: emit as-is, outside of markers
                result_parts.append(piece)
            else:
                # Non-separator text: wrap again in markers
                result_parts.append(f"{start}{piece}{end}")

        # Continue after the end marker
        i = e + len(end)

    return "".join(result_parts)


def _replace_unchanged_paragraphs_with_marker(
    text: str,
    deletion_marker: Tuple[str, str],
    insertion_marker: Tuple[str, str],
    omission_marker: str,
) -> str:
    """
    Replace contiguous runs of paragraphs that contain no diff markers with a
    single placeholder paragraph containing `omission_marker`.

    Paragraph separators are handled so that redundant sequential paragraph
    breaks are avoided (no extra blank lines appear solely due to omission).
    """
    del_start, _ = deletion_marker
    ins_start, _ = insertion_marker

    pieces = _PARAGRAPH_SEP_RE.split(text)
    result_parts: List[str] = []

    omitted_running = False
    omitted_sep: str = ""

    for i in range(0, len(pieces), 2):
        segment = pieces[i]
        separator = pieces[i + 1] if i + 1 < len(pieces) else ""

        has_change = (del_start in segment) or (ins_start in segment)

        if has_change:
            # If we have just skipped one or more unchanged paragraphs,
            # insert a single omission paragraph before this changed one.
            if omitted_running:
                # Avoid adding an extra blank line if we already end with a separator.
                if result_parts:
                    last = result_parts[-1]
                    if not _PARAGRAPH_SEP_RE.fullmatch(last):
                        result_parts.append("\n\n")
                # Omission placeholder itself.
                result_parts.append(omission_marker)
                # Separator following the placeholder (if any omitted paragraph had one).
                if omitted_sep or separator:
                    result_parts.append("\n\n")
                omitted_running = False
                omitted_sep = ""

            # Emit the changed paragraph as-is.
            result_parts.append(segment)
            if separator:
                result_parts.append(separator)
        else:
            # Unchanged paragraph: mark as part of an omitted run.
            if segment or separator:
                omitted_running = True
                # Track the most recent separator within the omitted run.
                if separator:
                    omitted_sep = separator

    # If the text ends with one or more omitted paragraphs, add a placeholder at the end.
    if omitted_running:
        if result_parts:
            last = result_parts[-1]
            if not _PARAGRAPH_SEP_RE.fullmatch(last):
                result_parts.append("\n\n")
        result_parts.append(omission_marker)
        # No extra trailing separator after the final placeholder.

    return "".join(result_parts)


def _drop_unchanged_paragraphs(
    text: str,
    deletion_marker: Tuple[str, str],
    insertion_marker: Tuple[str, str],
) -> str:
    """
    Remove paragraphs that contain no diff markers, along with their following
    paragraph separators. No placeholder is inserted.

    This corresponds to omission_marker == "" semantics.
    """
    del_start, _ = deletion_marker
    ins_start, _ = insertion_marker

    pieces = _PARAGRAPH_SEP_RE.split(text)
    result_parts: List[str] = []
    first_output = True

    for i in range(0, len(pieces), 2):
        segment = pieces[i]
        separator = pieces[i + 1] if i + 1 < len(pieces) else ""

        has_change = (del_start in segment) or (ins_start in segment)

        if has_change:
            # Keep changed paragraph and its separator.
            result_parts.append(segment)
            if separator:
                result_parts.append(separator)
            first_output = False
        else:
            # Drop unchanged paragraph and its following separator entirely.
            continue

    # If everything was unchanged, this should not be used (we guard earlier),
    # but if it happens, return the original text unchanged.
    if not result_parts:
        return text

    return "".join(result_parts)


def diff_texts_inline(
    original: str,
    modified: str,
    deletion_marker: Tuple[str, str] = ("[-", "-]"),
    insertion_marker: Tuple[str, str] = ("[+", "+]"),
    omission_marker: Optional[str] = "[...]",
) -> str:
    """
    Return a printable, word-level diff string between two multi-paragraph texts.

    Deletions are marked as:
        deletion_marker[0] + deleted_text + deletion_marker[1]

    Insertions are marked as:
        insertion_marker[0] + inserted_text + insertion_marker[1]

    Properties
    ----------
    - Works well for very large paragraphs with many sentences.
    - Changes are highlighted at word granularity.
    - Marked spans never cross paragraph boundaries (blank lines).
    - Unchanged paragraphs can be processed based on `omission_marker`:

        * omission_marker is None:
            All paragraphs (changed and unchanged) are included.

        * omission_marker == "":
            Paragraphs with no changes, and their following paragraph
            breaks, are removed entirely from the diff (no placeholder).

        * omission_marker is a non-empty string (e.g. "[...]"):
            Contiguous runs of unchanged paragraphs are replaced by a
            single placeholder paragraph containing `omission_marker`.
            Redundant sequential paragraph breaks around this placeholder
            are avoided.

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
    omission_marker : Optional[str], optional
        Controls omission of unchanged paragraphs as described above.
        Default is "[...]" (omit and collapse unchanged runs with a marker).

    Returns
    -------
    str
        A diff string with inline markers, preserving original whitespace
        within paragraphs and paragraph breaks, subject to omission behavior.
    """
    orig_tokens: List[str] = _tokenize_with_whitespace(original)
    mod_tokens: List[str] = _tokenize_with_whitespace(modified)

    sm = difflib.SequenceMatcher(a=orig_tokens, b=mod_tokens)
    parts: List[str] = []

    del_start, del_end = deletion_marker
    ins_start, ins_end = insertion_marker

    # First pass: word-level diff with inline markers.
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

    # Ensure markers do not cross paragraph boundaries.
    diff_text = _split_marked_spans_by_paragraphs(diff_text, deletion_marker)
    diff_text = _split_marked_spans_by_paragraphs(diff_text, insertion_marker)

    # If no changes at all, return the original text (no markers, no omission).
    if del_start not in diff_text and ins_start not in diff_text:
        return original

    # Handle unchanged paragraphs according to omission_marker.
    if omission_marker is None:
        # Keep all paragraphs as-is.
        return diff_text
    elif omission_marker == "":
        # Drop unchanged paragraphs and their following separators.
        return _drop_unchanged_paragraphs(
            diff_text,
            deletion_marker=deletion_marker,
            insertion_marker=insertion_marker,
        )
    else:
        # Replace runs of unchanged paragraphs with a placeholder paragraph.
        return _replace_unchanged_paragraphs_with_marker(
            diff_text,
            deletion_marker=deletion_marker,
            insertion_marker=insertion_marker,
            omission_marker=omission_marker,
        )


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