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

    Example transformation:

        [-First paragraph text.\n\nSecond paragraph text.-]

    becomes:

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
    single placeholder line containing `omission_marker`.

    The placeholder appears on its own line with no completely blank line
    before or after it.
    """
    del_start, _ = deletion_marker
    ins_start, _ = insertion_marker

    pieces = _PARAGRAPH_SEP_RE.split(text)
    n_segments = (len(pieces) + 1) // 2

    segments = [pieces[2 * i] for i in range(n_segments)]
    seps = [pieces[2 * i + 1] if 2 * i + 1 < len(pieces) else "" for i in range(n_segments)]
    changed = [(del_start in seg) or (ins_start in seg) for seg in segments]

    changed_indices = [i for i, c in enumerate(changed) if c]
    if not changed_indices:
        return text

    first_changed = changed_indices[0]
    last_changed = changed_indices[-1]

    result_parts: List[str] = []

    # Leading unchanged run before first_changed
    if first_changed > 0:
        result_parts.append(omission_marker)
        if first_changed <= last_changed:
            result_parts.append("\n")

    i = first_changed
    while i <= last_changed:
        if not changed[i]:
            i += 1
            continue

        # Append current changed segment
        result_parts.append(segments[i])

        # Determine range of following unchanged run (within [0, n_segments))
        j = i + 1
        while j < n_segments and not changed[j] and j <= last_changed:
            j += 1

        if j == i + 1:
            # No unchanged run immediately after within the processed range:
            # keep original separator.
            result_parts.append(seps[i])
            i += 1
        else:
            # There is an unchanged run i+1..j-1 we omit.
            if j <= last_changed:
                # Another changed paragraph after the omitted run:
                #   segment[i] + "\n" + marker + "\n" + segment[j]
                if not result_parts[-1].endswith("\n"):
                    result_parts.append("\n")
                result_parts.append(omission_marker)
                result_parts.append("\n")
            else:
                # Omitted run goes through or beyond last_changed (no more changed
                # paragraphs to emit).
                if not result_parts[-1].endswith("\n"):
                    result_parts.append("\n")
                result_parts.append(omission_marker)
            i = j

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

    for i in range(0, len(pieces), 2):
        segment = pieces[i]
        separator = pieces[i + 1] if i + 1 < len(pieces) else ""
        has_change = (del_start in segment) or (ins_start in segment)

        if has_change:
            result_parts.append(segment)
            if separator:
                result_parts.append(separator)

    if not result_parts:
        return text

    return "".join(result_parts)


def _normalize_diff_output(text: str, omission_marker: Optional[str]) -> str:
    """
    Post-process the diff output to:
      - remove redundant blank lines around the omission marker (if used),
      - and remove trailing empty lines altogether.
    """
    if omission_marker:
        om_esc = re.escape(omission_marker)
        # Collapse multiple blank lines before the marker to a single newline.
        text = re.sub(r"(\n\s*)+\n(" + om_esc + r")", r"\n\2", text)
        # Collapse multiple blank lines after the marker to a single newline.
        text = re.sub(r"(" + om_esc + r")\n(\n\s*)+", r"\1\n", text)

    # Remove trailing completely blank lines (one or more).
    text = re.sub(r"(\n[ \t]*)+\Z", "", text)
    return text


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
            single placeholder line containing `omission_marker`, with
            no completely blank line before or after the placeholder.

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
        within paragraphs and paragraph breaks, subject to omission behavior,
        and with no trailing empty lines.
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
        # Keep all paragraphs as-is, then normalize trailing empties.
        return _normalize_diff_output(diff_text, omission_marker)
    elif omission_marker == "":
        # Drop unchanged paragraphs and their following separators.
        text = _drop_unchanged_paragraphs(
            diff_text,
            deletion_marker=deletion_marker,
            insertion_marker=insertion_marker,
        )
        return _normalize_diff_output(text, omission_marker)
    else:
        # Replace runs of unchanged paragraphs with a placeholder line.
        text = _replace_unchanged_paragraphs_with_marker(
            diff_text,
            deletion_marker=deletion_marker,
            insertion_marker=insertion_marker,
            omission_marker=omission_marker,
        )
        return _normalize_diff_output(text, omission_marker)


if __name__ == "__main__":
    v1 = "This is a very long paragraph that contains several sentences. This sentence stays unchanged. Some of the sentences will change slightly.\n\nHere is another paragraph that stays mostly the same.\n\nThis paragraph stays entirely unchanged.\n\nThis sentence will add something new.\n\nThis one will be deleted."

    v2 = "This is a very long paragraph that contains many sentences. This sentence stays unchanged. Some of these sentences will change slightly.\n\nHere is another paragraph that stays almost the same.\n\nThis paragraph stays entirely unchanged.\n\nThis sentence will add something new..."

    print(diff_texts_inline(v1, v2))
