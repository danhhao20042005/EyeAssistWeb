from app.pipeline.reading_order import reading_order
from app.schemas import BBox, Block


def block(name: str, x: int, y: int, w: int, h: int) -> Block:
    return Block(id=name, type="paragraph", page=0, bbox=BBox(x=x, y=y, w=w, h=h))


def ids(blocks: list[Block]) -> list[str]:
    return [b.id for b in blocks]


def test_two_columns_read_column_by_column():
    blocks = [
        block("title", 100, 80, 1000, 50),
        block("r1", 660, 300, 490, 100),
        block("l1", 90, 300, 490, 100),
        block("l2", 90, 450, 490, 100),
        block("r2", 660, 450, 490, 100),
        block("footer", 90, 1100, 1060, 30),
    ]
    assert ids(reading_order(blocks, 1240, 1754)) == ["title", "l1", "l2", "r1", "r2", "footer"]


def test_single_column_reads_top_to_bottom():
    blocks = [block("c", 100, 600, 800, 50), block("a", 100, 100, 800, 50), block("b", 100, 300, 800, 50)]
    assert ids(reading_order(blocks, 1000, 1400)) == ["a", "b", "c"]


def test_three_columns():
    blocks = [block(f"c{c}r{r}", 60 + c * 400, 200 + r * 150, 340, 120) for c in range(3) for r in range(2)]
    shuffled = blocks[::-1]
    assert ids(reading_order(shuffled, 1300, 1000)) == ["c0r0", "c0r1", "c1r0", "c1r1", "c2r0", "c2r1"]


def test_staggered_columns_keep_column_order():
    blocks = [
        block("l1", 90, 200, 490, 300),
        block("r1", 660, 200, 490, 120),
        block("r2", 660, 380, 490, 120),
        block("l2", 90, 560, 490, 100),
    ]
    assert ids(reading_order(blocks, 1240, 1754)) == ["l1", "l2", "r1", "r2"]


def test_empty_and_single():
    assert reading_order([], 100, 100) == []
    only = block("x", 0, 0, 10, 10)
    assert reading_order([only], 100, 100) == [only]
