import shutil

import pytest

from tests import synth


def _has_vie() -> bool:
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract

        return "vie" in pytesseract.get_languages(config="")
    except Exception:
        return False


needs_ocr = pytest.mark.skipif(
    not (_has_vie() and synth.have_fonts()),
    reason="Cần Tesseract kèm dữ liệu tiếng Việt (vie) và phông chữ DejaVu hoặc Arial",
)
