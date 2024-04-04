def split_text_by_paragraphs_and_limit(text: str, limit: int) -> list[str]:
    """Return a given text split into segments based on paragraph breaks, ensuring that each segment does not exceed a specified character limit.

    The function processes a text string, splitting it into paragraphs and then grouping these paragraphs into segments.
    Each segment is constructed to be as large as possible without surpassing a given character limit.
    This method guarantees that individual paragraphs are not split across different segments, maintaining the integrity of the text's structure.

    Parameters:
    - text (str): The input text to be split. The text is expected to have paragraphs separated by two newline characters ("\n\n").
    - limit (int): The maximum number of characters allowed in each segment. This limit should be chosen considering that no single paragraph exceeds it, as the function does not split individual paragraphs.

    Returns:
    - list[str]: A list of text segments, each containing one or more complete paragraphs and not exceeding the specified character limit.

    Raises:
    - AssertionError: If any individual paragraph exceeds the specified character limit. This is a precaution to ensure that the function can operate without needing to split any single paragraph.

    Note:
    - This function is particularly useful for processing large texts for display or analysis, where maintaining the structural integrity of paragraphs is important, and a certain size constraint for segments is required.
    """
    if len(text) <= limit:
        return [text]

    paragraphs = text.split("\n\n")
    for paragraph in paragraphs:
        assert len(paragraph) <= limit, (len(paragraph), paragraph)

    result = []
    current_part = ""

    for paragraph in paragraphs:
        candidate = f"{current_part}\n\n{paragraph}" if current_part else paragraph

        if len(candidate) > limit:
            result.append(current_part)
            current_part = paragraph
        else:
            current_part = candidate

    if current_part:
        result.append(current_part)
    return result
