# backend/preprocessing.py

import re
from typing import List

STOPWORDS = {"the", "a", "an", "is", "are", "of", "in", "to", "and"}  # extend later

class PromptCleaner:
    def __init__(self, enable_spelling: bool = False):
        self.enable_spelling = enable_spelling
        # optionally init spelling corrector library here later

    def normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def lowercase(self, text: str) -> str:
        return text.lower()

    def remove_noise_chars(self, text: str) -> str:
        # remove weird symbols, keep basic punctuation
        return re.sub(r"[^a-zA-Z0-9\s,.?%]", " ", text)

    def remove_stopwords(self, text: str) -> str:
        tokens = text.split()
        filtered = [t for t in tokens if t.lower() not in STOPWORDS]
        return " ".join(filtered)

    def clean(self, text: str) -> str:
        text = self.normalize_whitespace(text)
        text = self.lowercase(text)
        text = self.remove_noise_chars(text)
        text = self.remove_stopwords(text)

        if self.enable_spelling:
            # TODO: integrate spelling library later
            pass

        return text