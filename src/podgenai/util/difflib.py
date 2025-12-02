import difflib
import re


def _tokenize_with_whitespace(text: str) -> list[str]:
    """
    Split text into a sequence of tokens preserving all whitespace.

    Each token is either:
    - a run of non-whitespace characters (a word/punctuation), or
    - a run of whitespace characters (spaces, newlines, tabs, etc.).
    """
    return re.findall(r"\S+|\s+", text)


def diff_texts_inline(
    original: str,
    modified: str,
    *,
    deletion_marker: tuple[str, str] = ("[-", "-]"),
    insertion_marker: tuple[str, str] = ("[+", "+]"),
) -> str:
    """
    Return a printable, word-level diff string between two multi-paragraph texts.

    Deletions are marked as:  deletion_marker[0] + deleted_text + deletion_marker[1]
    Insertions are marked as: insertion_marker[0] + inserted_text + insertion_marker[1]

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

    return "".join(parts)


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