import logging
from pathlib import Path

from latex_music_linker import agent as agent_module
from latex_music_linker import core


def test_agent_fallback_to_heuristic(monkeypatch, caplog):
    def fake_resolve(entities, *, country="us"):
        for e in entities:
            e.smartlink_url = f"https://example.test/{e.name}"
        return entities

    monkeypatch.setattr(core, "resolve_entities", fake_resolve)

    caplog.set_level(logging.WARNING, logger=core.LOG.name)
    latex = r"Artist's \album{Some Album}"
    linked = core.process_latex_string(latex, agent_name="missing-agent")

    assert "\\href" in linked
    assert any("falling back" in message for message in caplog.messages)


def test_stub_agent_receives_candidates(monkeypatch):
    seen_artists = []

    def fake_resolve(entities, *, country="us"):
        seen_artists.extend([e.artist for e in entities])
        for e in entities:
            e.smartlink_url = "https://example.test/link"
        return entities

    monkeypatch.setattr(core, "resolve_entities", fake_resolve)

    class StubStrategy(agent_module.AgentStrategy):
        name = "stub"

        def enrich(self, latex: str, candidates):
            for c in candidates:
                c.artist = "Stub Artist"
            return candidates

    monkeypatch.setattr(agent_module, "agent_factories", lambda: {"stub": StubStrategy})

    latex = r"Artist wrote \song{Song}"
    core.process_latex_string(latex, agent_name="stub")

    assert seen_artists and all(artist == "Stub Artist" for artist in seen_artists)


def test_newsletter_example_links(monkeypatch):
    url_map = {
        "God Does Like Ugly": "https://album.link/i/1832251919",
        "Gz": "https://song.link/i/1812517950",
    }

    def fake_resolve(entities, *, country="us"):
        for e in entities:
            e.smartlink_url = url_map.get(e.name)
        return entities

    monkeypatch.setattr(core, "resolve_entities", fake_resolve)

    latex = Path("examples/newsletter_example.tex").read_text(encoding="utf-8")
    expected = Path("examples/newsletter_example_linked.tex").read_text(encoding="utf-8")

    linked = core.process_latex_string(latex, agent_name="heuristic")
    assert linked == expected
