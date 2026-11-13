from app.pipeline.table import grid_from_words
from app.schemas import BBox, Word


def word(text: str, x: int, y: int, w: int = 80, h: int = 24) -> Word:
    return Word(text=text, conf=0.9, bbox=BBox(x=x, y=y, w=w, h=h))


def test_borderless_grid_from_words():
    words = [
        word("Mảng", 10, 10), word("Quý", 300, 10, 50), word("2", 360, 10, 20), word("Quý", 600, 10, 50), word("3", 660, 10, 20),
        word("Bán", 10, 60, 50), word("lẻ", 70, 60, 30), word("40", 300, 60, 30), word("41", 600, 60, 30),
    ]
    assert grid_from_words(words) == [["Mảng", "Quý 2", "Quý 3"], ["Bán lẻ", "40", "41"]]


def test_empty_words():
    assert grid_from_words([]) == []
