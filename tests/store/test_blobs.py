from pathlib import Path

from meridian.config import Settings
from meridian.store import blobs


def test_save_blob_writes_bytes(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    data = b"pdf-bytes"
    path = blobs.save(data, name="sample.pdf", settings=settings)
    assert path.parent == settings.data_dir / "documents"
    assert path.name == "sample.pdf"
    assert path.read_bytes() == data
