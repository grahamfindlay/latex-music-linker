from latex_music_linker.parsing import find_candidates


def test_find_candidates_basic():
    latex = r"Artist's \album{Some Album} (2020) and \song{Hit Single}."
    entities = find_candidates(latex)
    names = [e.name for e in entities]
    assert "Some Album" in names
    assert "Hit Single" in names


def test_find_candidates_skips_href_wrapped_song():
    """Songs already wrapped in \\href should not be extracted."""
    latex = r"\href{https://song.link/i/1479414074}{\song{riot in Lagos}}"
    entities = find_candidates(latex)
    assert len(entities) == 0


def test_find_candidates_skips_href_wrapped_album():
    """Albums already wrapped in \\href should not be extracted."""
    latex = r"\href{https://album.link/i/123456}{\album{Some Album}}"
    entities = find_candidates(latex)
    assert len(entities) == 0


def test_find_candidates_skips_gref_wrapped_song():
    """Songs already wrapped in \\gref should not be extracted."""
    latex = r"\gref{https://song.link/i/1479414074}{\song{riot in Lagos}}"
    entities = find_candidates(latex)
    assert len(entities) == 0


def test_find_candidates_skips_gref_wrapped_album():
    """Albums already wrapped in \\gref should not be extracted."""
    latex = r"\gref{https://album.link/i/123456}{\album{Some Album}}"
    entities = find_candidates(latex)
    assert len(entities) == 0


def test_find_candidates_mixed_linked_and_unlinked():
    """Only unlinked entities should be extracted when mixed with linked ones."""
    latex = (
        r"Check out \href{https://song.link/i/123}{\song{Already Linked}} "
        r"and also \song{New Song} from \album{New Album}."
    )
    entities = find_candidates(latex)
    names = [e.name for e in entities]
    assert "Already Linked" not in names
    assert "New Song" in names
    assert "New Album" in names
    assert len(entities) == 2
