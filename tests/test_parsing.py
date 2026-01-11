from latex_music_linker.parsing import find_candidates, find_failed_links


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


def test_find_failed_links_finds_notfound_song():
    """Should find songs wrapped in song.link/not-found hrefs."""
    latex = r"\href{https://song.link/not-found}{\song{Future Legend}}"
    entities = find_failed_links(latex)
    assert len(entities) == 1
    assert entities[0].name == "Future Legend"
    assert entities[0].type == "track"
    assert entities[0].latex_text == r"\song{Future Legend}"


def test_find_failed_links_finds_notfound_album():
    """Should find albums wrapped in song.link/not-found hrefs."""
    latex = r"\href{https://song.link/not-found}{\album{Diamond Dogs}}"
    entities = find_failed_links(latex)
    assert len(entities) == 1
    assert entities[0].name == "Diamond Dogs"
    assert entities[0].type == "album"
    assert entities[0].latex_text == r"\album{Diamond Dogs}"


def test_find_failed_links_ignores_successful_links():
    """Should not match successfully resolved links."""
    latex = r"\href{https://song.link/i/123456}{\song{Successful Song}}"
    entities = find_failed_links(latex)
    assert len(entities) == 0


def test_find_failed_links_mixed():
    """Should only find failed links when mixed with successful ones."""
    latex = (
        r"\href{https://song.link/not-found}{\song{Failed Song}} "
        r"\href{https://album.link/i/999}{\album{Good Album}} "
        r"\href{https://song.link/not-found}{\album{Failed Album}}"
    )
    entities = find_failed_links(latex)
    assert len(entities) == 2
    names = [e.name for e in entities]
    assert "Failed Song" in names
    assert "Failed Album" in names
    assert "Good Album" not in names


def test_find_failed_links_tracks_positions():
    """Should track correct start/end positions for replacement."""
    latex = r"Before \href{https://song.link/not-found}{\song{Test}} after"
    entities = find_failed_links(latex)
    assert len(entities) == 1
    e = entities[0]
    # Verify the span covers the entire href wrapper
    assert latex[e.start_index:e.end_index] == r"\href{https://song.link/not-found}{\song{Test}}"
