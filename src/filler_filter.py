"""
MWhisper Filler Word Filter
Removes filler words like "uh", "um", "эээ" from transcribed text
"""

import re
from typing import List, Tuple


# Filler word patterns for different languages
FILLER_PATTERNS: List[Tuple[str, str]] = [
    # Russian fillers
    (r'\b[эе]+\b', ''),           # э, ээ, эээ
    (r'\b[аa]+\b', ''),           # а, аа
    (r'\bхм+\b', ''),             # хм, хмм
    (r'\bмм+\b', ''),             # мм, ммм
    (r'\bну+\b', ''),             # ну (when standalone filler)
    (r'\bвот\b', ''),             # вот (filler usage)
    (r'\bтипа\b', ''),            # типа
    (r'\bкак бы\b', ''),          # как бы
    (r'\bкороче\b', ''),          # короче
    
    # English fillers
    (r'\buh+\b', ''),             # uh, uhh
    (r'\bum+\b', ''),             # um, umm
    (r'\buhm+\b', ''),            # uhm
    (r'\bah+\b', ''),             # ah, ahh
    (r'\ber+\b', ''),             # er, err
    (r'\blike\b(?=\s*,)', ''),    # like, (filler usage)
    (r'\byou know\b', ''),        # you know
    (r'\bi mean\b', ''),          # i mean
    (r'\bso+\b(?=\s*,)', ''),     # so, (filler at start)
    
    # German fillers
    (r'\bähm?\b', ''),            # äh, ähm
    (r'\böhm?\b', ''),            # öh, öhm
    (r'\bhm+\b', ''),             # hm, hmm
    
    # Spanish fillers
    (r'\beh+\b', ''),             # eh
    (r'\beste+\b', ''),           # este
    (r'\bbueno\b(?=\s*,)', ''),   # bueno,
    
    # French fillers
    (r'\beuh+\b', ''),            # euh
    (r'\bben\b', ''),             # ben
    (r'\bgenre\b', ''),           # genre
]

# Compiled patterns for efficiency
_compiled_patterns: List[Tuple[re.Pattern, str]] = []


def _ensure_compiled() -> None:
    """Compile regex patterns if not already done"""
    global _compiled_patterns
    if not _compiled_patterns:
        _compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in FILLER_PATTERNS
        ]


def filter_fillers(text: str, enabled: bool = True) -> str:
    """
    Remove filler words from text.
    
    Args:
        text: Input text with potential filler words
        enabled: If False, return text unchanged
    
    Returns:
        Text with filler words removed
    """
    if not enabled or not text:
        return text
    
    _ensure_compiled()
    
    result = text
    for pattern, replacement in _compiled_patterns:
        result = pattern.sub(replacement, result)
    
    # Clean up multiple spaces and punctuation issues
    result = re.sub(r'\s+', ' ', result)  # Multiple spaces to one
    result = re.sub(r'\s+([,.!?])', r'\1', result)  # Space before punctuation
    result = re.sub(r'([,.!?])\s*([,.!?])', r'\1', result)  # Double punctuation
    result = re.sub(r'^\s*[,.]\s*', '', result)  # Leading comma/period
    result = result.strip()
    
    # Capitalize first letter if needed
    if result and result[0].islower():
        result = result[0].upper() + result[1:]
    
    return result


def add_custom_filler(pattern: str, replacement: str = '') -> None:
    """
    Add a custom filler pattern.
    
    Args:
        pattern: Regex pattern to match
        replacement: Replacement text (usually empty)
    """
    global _compiled_patterns
    _ensure_compiled()
    _compiled_patterns.append(
        (re.compile(pattern, re.IGNORECASE), replacement)
    )


def get_filler_patterns() -> List[str]:
    """Get list of current filler patterns"""
    return [pattern for pattern, _ in FILLER_PATTERNS]


# Example usage and testing
if __name__ == "__main__":
    test_cases = [
        "Ээ, я думаю, что это хорошая идея",
        "Um, I think, uh, we should go",
        "Хм, ну вот, типа, не знаю",
        "So, like, you know, it's complicated",
        "Äh ich glaube das ist gut",
    ]
    
    print("Filler Filter Test:")
    print("-" * 50)
    for text in test_cases:
        filtered = filter_fillers(text)
        print(f"Input:  {text}")
        print(f"Output: {filtered}")
        print()
