# tests/test_preprocessing.py

from backend.preprocessing import PromptCleaner


def test_clean_removes_extra_spaces_and_lowercases():
    cleaner = PromptCleaner()

    raw = "   Total   SALES   in   2023   "
    cleaned = cleaner.clean(raw)

    # should be lowercased
    assert cleaned == cleaned.lower()

    # should not have double spaces
    assert "  " not in cleaned

    # core meaning should still contain the key words
    assert "total" in cleaned
    assert "sales" in cleaned
    assert "2023" in cleaned


def test_clean_removes_stopwords():
    cleaner = PromptCleaner()

    raw = "What is the total sales in 2023?"
    cleaned = cleaner.clean(raw)

    # 'the' and 'in' are in our stopword list, so they should be removed
    assert "the" not in cleaned.split()
    assert "in" not in cleaned.split()

    # Important content words should still be there
    tokens = cleaned.split()
    assert "total" in tokens
    assert "sales" in tokens or "sale" in tokens
    assert any("2023" in t for t in tokens)


def test_remove_noise_characters():
    cleaner = PromptCleaner()

    raw = "Total $ales!!! in 2023 #@*"
    cleaned = cleaner.clean(raw)

    # No weird symbols
    for ch in cleaned:
        assert ch.isalnum() or ch.isspace() or ch in {",", ".", "?", "%"}