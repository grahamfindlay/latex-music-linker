from latex_music_linker.parsing import MusicEntity, apply_links_to_latex


def test_apply_links_to_latex_wraps_entities():
    latex = r"Artist's \\textit{Some Album}"
    e = MusicEntity(
        name="Some Album",
        artist="Artist",
        type="album",
        year=None,
        latex_text="\\textit{Some Album}",
        start_index=9,
        end_index=len(latex),
        platform_url="URL",
        smartlink_url="https://album.link/example",
    )
    linked = apply_links_to_latex(latex, [e])
    assert "href" in linked
    assert "Some Album" in linked
