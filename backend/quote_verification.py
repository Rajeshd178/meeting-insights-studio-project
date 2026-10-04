"""
Transcript Quote Verification Helper.
Provides normalized fuzzy match using difflib to verify that model claims
reference verbatim or near-verbatim segments from the transcript.
"""

import re
import difflib
from typing import Union, List


def normalize_text(text: str) -> str:
    """Strip punctuation and whitespace for normalized comparison."""
    if not text:
        return ""
    # Lowercase, replace smart quotes, remove non-alphanumeric except spaces
    cleaned = text.lower().replace('“', '"').replace('”', '"').replace("’", "'")
    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
    return " ".join(cleaned.split())


def quote_exists(quote: str, transcript: Union[str, List[str]], threshold: float = 0.70) -> bool:
    """
    Verifies that a quote exists in the transcript using exact substring containment
    or normalized fuzzy matching with difflib.
    """
    if not quote or len(quote.strip()) < 3:
        return False

    if isinstance(transcript, list):
        full_transcript = " ".join([str(t) for t in transcript if t])
    else:
        full_transcript = str(transcript or "")

    norm_quote = normalize_text(quote)
    norm_transcript = normalize_text(full_transcript)

    if not norm_quote or not norm_transcript:
        return False

    # 1. Exact normalized substring match
    if norm_quote in norm_transcript:
        return True

    # 2. Key phrase / half-phrase check for longer quotes
    words = norm_quote.split()
    if len(words) >= 4:
        half = len(words) // 2
        p1 = " ".join(words[:half])
        p2 = " ".join(words[half:])
        if p1 in norm_transcript or p2 in norm_transcript:
            return True

    # 3. Sliding window fuzzy matching using difflib
    quote_len = len(norm_quote)
    step = max(5, quote_len // 3)
    best_ratio = 0.0

    for i in range(0, max(1, len(norm_transcript) - quote_len + step), step):
        window = norm_transcript[i:i + quote_len + 20]
        matcher = difflib.SequenceMatcher(None, norm_quote, window)
        ratio = matcher.ratio()
        if ratio > best_ratio:
            best_ratio = ratio
        if best_ratio >= threshold:
            return True

    return best_ratio >= threshold
