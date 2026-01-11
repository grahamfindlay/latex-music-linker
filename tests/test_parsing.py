from latex_music_linker.parsing import find_candidates


def test_find_candidates_basic():
    latex = r"Artist's \album{Some Album} (2020) and \song{Hit Single}."
    entities = find_candidates(latex)
    names = [e.name for e in entities]
    assert "Some Album" in names
    assert "Hit Single" in names
