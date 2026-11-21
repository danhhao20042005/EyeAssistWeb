from pathlib import Path
import shutil

import pytest

from tests import synth


def _has_vie() -> bool:
    try:
        from app.pipeline.ocr import _configure_tesseract
        _configure_tesseract()
        import pytesseract
        cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "tesseract")
        if shutil.which(cmd) is None and not Path(cmd).exists():
            return False
        return "vie" in pytesseract.get_languages(config="")
    except Exception:
        return False


needs_ocr = pytest.mark.skipif(
    not (_has_vie() and synth.have_fonts()),
    reason="Cần Tesseract kèm dữ liệu tiếng Việt (vie) và phông chữ DejaVu hoặc Arial",
)
