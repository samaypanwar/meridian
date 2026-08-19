from meridian.kb.searchable import build_searchable_text


def test_build_searchable_text_includes_framing_and_body() -> None:
    text = build_searchable_text(
        title="Example Talk",
        url="https://youtube.com/watch?v=abc",
        genre="video",
        source_type="youtube",
        platform="youtube",
        normalized_text="Policy gradients estimate improvement direction.",
        framing_json='{"point": "RL overview", "matters_for_goals": "Foundations lane"}',
        theme_breakdown_json='{"foundations/rl": 8, "frontier/agentic-harnesses": 0}',
    )
    assert "rl overview" in text
    assert "foundations rl" in text
    assert "policy gradients" in text
    assert "agentic" not in text
