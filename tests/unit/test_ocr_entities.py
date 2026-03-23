from app.services.ai import VisionProvider


def test_extract_entities_from_text_fixture():
    r = VisionProvider().extract("tests/fixtures/sample.txt")
    assert r.entities["inn"] == ["123456789012"]
    assert r.entities["full_names"]
