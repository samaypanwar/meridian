from pathlib import Path

from meridian.config import Settings
from meridian.store import vault


def test_write_extraction_writes_dated_slug(tmp_path: Path) -> None:
    settings = Settings(capture_path=tmp_path / "vault" / "learnings" / "meridian")
    note_md = "---\ntype: extraction\n---\n\n# Test note\n"
    path = vault.write_extraction(note_md, slug="test-topic", settings=settings)
    assert path.parent == settings.capture_path
    assert path.name.startswith("extraction-")
    assert "test-topic" in path.name
    assert path.suffix == ".md"
    assert path.read_text() == note_md


def test_iter_extractions_yields_written_notes(tmp_path: Path) -> None:
    settings = Settings(capture_path=tmp_path / "vault" / "learnings" / "meridian")
    note_md = "# Note\n"
    written = vault.write_extraction(note_md, slug="alpha", settings=settings)
    found = list(vault.iter_extractions(settings=settings))
    assert written in found
