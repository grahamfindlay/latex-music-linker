from pathlib import Path

from latex_music_linker.parsing import MusicEntity, apply_links_to_latex, find_candidates


def test_apply_links_to_latex_wraps_entities():
    latex = r"Artist's \album{Some Album}"
    e = MusicEntity(
        name="Some Album",
        artist="Artist",
        type="album",
        year=None,
        latex_text="\\album{Some Album}",
        start_index=9,
        end_index=len(latex),
        platform_url="URL",
        smartlink_url="https://album.link/example",
    )
    linked = apply_links_to_latex(latex, [e])
    assert "href" in linked
    assert "Some Album" in linked


def test_apply_links_to_latex_with_sample_data():
    base = Path(__file__).parent / "data"
    latex = (base / "sample.tex").read_text(encoding="utf-8")
    expected = (base / "sample_linked_expected.tex").read_text(encoding="utf-8")

    entities = find_candidates(latex)
    url_map = {
        "God Does Like Ugly": "https://album.link/i/1832251919",
        "Gz": "https://song.link/i/1812517950",
    }
    for e in entities:
        e.smartlink_url = url_map.get(e.name)

    linked = apply_links_to_latex(latex, entities)
    assert linked == expected
