from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import asdict
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Callable

from .parsing import MusicEntity

LOG = logging.getLogger(__name__)


class AgentError(RuntimeError):
    """Raised when an agent cannot enrich entities."""


class AgentStrategy:
    """Interface for agent strategies."""

    name = "base"

    def enrich(self, latex: str, candidates: list[MusicEntity]) -> list[MusicEntity]:
        raise NotImplementedError


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_prompt_path() -> Path:
    return _project_root() / "docs" / "prompts" / "agent_prompt.md"


def default_tools_path() -> Path:
    return _project_root() / "docs" / "tools" / "music_resolvers.yaml"


class HeuristicStrategy(AgentStrategy):
    """Return the heuristic candidates unchanged."""

    name = "heuristic"

    def enrich(self, latex: str, candidates: list[MusicEntity]) -> list[MusicEntity]:
        return candidates


class LLMStrategy(AgentStrategy):
    """Call an external LLM via the `llm` CLI to enrich entities."""

    name = "llm"

    def __init__(
        self,
        model: str | None = None,
        prompt_path: str | Path | None = None,
        tools_path: str | Path | None = None,
        llm_binary: str = "llm",
        extra_args: list[str] | None = None,
    ) -> None:
        self.model = model or "gpt-4o-mini"
        self.prompt_path = Path(prompt_path) if prompt_path else default_prompt_path()
        self.tools_path = Path(tools_path) if tools_path else default_tools_path()
        self.llm_binary = llm_binary
        self.extra_args = extra_args or []

    def _system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise AgentError(f"Prompt file not found: {self.prompt_path}")
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AgentError(f"Unable to read prompt file: {self.prompt_path}") from exc
        tools = ""
        try:
            if self.tools_path.exists():
                tools = self.tools_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AgentError(f"Unable to read tool schema file: {self.tools_path}") from exc
        header = "Tool schema (YAML):\n" if tools else ""
        return f"{prompt}\n\n{header}{tools}".strip()

    def _serialize_candidates(self, candidates: list[MusicEntity]) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": idx,
                **asdict(c),
            }
            for idx, c in enumerate(candidates)
        ]

    def _run_llm(self, system_prompt: str, payload: str) -> str:
        if not shutil.which(self.llm_binary):
            raise AgentError("llm CLI is not available on PATH")

        cmd = [self.llm_binary, "-m", self.model, "-s", system_prompt]
        cmd.extend(self.extra_args)
        cmd.append(payload)

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise AgentError(
                f"llm command failed with code {proc.returncode}: {proc.stderr.strip()}"
            )

        output = proc.stdout.strip()
        if not output:
            raise AgentError("llm produced no output")

        return output

    def _merge_entities(
        self, raw_entities: list[dict[str, Any]], base_candidates: list[MusicEntity]
    ) -> list[MusicEntity]:
        indexed = {idx: c for idx, c in enumerate(base_candidates)}
        merged: list[MusicEntity] = []

        def _coerce_int(value: Any, default: int) -> int:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str) and value.strip().isdigit():
                return int(value.strip())
            return default

        for item in raw_entities:
            if not isinstance(item, dict):
                continue

            candidate_id = item.get("candidate_id")
            if isinstance(candidate_id, str) and candidate_id.isdigit():
                candidate_id = int(candidate_id)

            candidate = indexed.get(candidate_id)
            if not candidate and "latex_text" in item:
                candidate = next(
                    (c for c in base_candidates if c.latex_text == item["latex_text"]), None
                )

            if not candidate:
                # Skip unknown spans to avoid corrupting offsets.
                continue

            year_val = item.get("year", candidate.year)
            if isinstance(year_val, str):
                cleaned_year = year_val.strip()
                if cleaned_year.isdigit():
                    year_val = int(cleaned_year)
                else:
                    year_val = candidate.year

            merged.append(
                MusicEntity(
                    name=item.get("name") or candidate.name,
                    artist=item.get("artist") or candidate.artist,
                    type=item.get("type") or candidate.type,
                    year=year_val,
                    latex_text=item.get("latex_text", candidate.latex_text),
                    start_index=_coerce_int(item.get("start_index"), candidate.start_index),
                    end_index=_coerce_int(item.get("end_index"), candidate.end_index),
                )
            )

        return merged

    def enrich(self, latex: str, candidates: list[MusicEntity]) -> list[MusicEntity]:
        system_prompt = self._system_prompt()
        payload = json.dumps(
            {
                "latex": latex,
                "candidates": self._serialize_candidates(candidates),
                "instruction_version": self.prompt_path.name,
            }
        )

        output = self._run_llm(system_prompt, payload)

        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise AgentError("Agent response was not valid JSON") from exc

        if isinstance(data, dict) and "entities" in data:
            raw_entities = data["entities"]
        elif isinstance(data, list):
            raw_entities = data
        else:
            raise AgentError("Agent response missing entities list")

        merged = self._merge_entities(raw_entities, candidates)
        if not merged:
            raise AgentError("Agent returned no usable entities")

        return merged


class ClaudeCodeStrategy(AgentStrategy):
    """Call Claude via the Claude Code CLI to enrich entities."""

    name = "claude-code"

    def __init__(
        self,
        prompt_path: str | Path | None = None,
        tools_path: str | Path | None = None,
        claude_binary: str = "claude",
    ) -> None:
        self.prompt_path = Path(prompt_path) if prompt_path else default_prompt_path()
        self.tools_path = Path(tools_path) if tools_path else default_tools_path()
        self.claude_binary = claude_binary

    def _system_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise AgentError(f"Prompt file not found: {self.prompt_path}")
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AgentError(f"Unable to read prompt file: {self.prompt_path}") from exc
        tools = ""
        try:
            if self.tools_path.exists():
                tools = self.tools_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise AgentError(f"Unable to read tool schema file: {self.tools_path}") from exc
        header = "Tool schema (YAML):\n" if tools else ""
        return f"{prompt}\n\n{header}{tools}".strip()

    def _serialize_candidates(self, candidates: list[MusicEntity]) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": idx,
                **asdict(c),
            }
            for idx, c in enumerate(candidates)
        ]

    def _run_claude(self, system_prompt: str, payload: str) -> str:
        if not shutil.which(self.claude_binary):
            raise AgentError("claude CLI is not available on PATH")

        cmd = [self.claude_binary, "--print", "-p", system_prompt, payload]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise AgentError(
                f"claude command failed with code {proc.returncode}: {proc.stderr.strip()}"
            )

        output = proc.stdout.strip()
        if not output:
            raise AgentError("claude produced no output")

        return output

    def _merge_entities(
        self, raw_entities: list[dict[str, Any]], base_candidates: list[MusicEntity]
    ) -> list[MusicEntity]:
        indexed = {idx: c for idx, c in enumerate(base_candidates)}
        merged: list[MusicEntity] = []

        def _coerce_int(value: Any, default: int) -> int:
            if value is None:
                return default
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str) and value.strip().isdigit():
                return int(value.strip())
            return default

        for item in raw_entities:
            if not isinstance(item, dict):
                continue

            candidate_id = item.get("candidate_id")
            if isinstance(candidate_id, str) and candidate_id.isdigit():
                candidate_id = int(candidate_id)

            candidate = indexed.get(candidate_id)
            if not candidate and "latex_text" in item:
                candidate = next(
                    (c for c in base_candidates if c.latex_text == item["latex_text"]), None
                )

            if not candidate:
                # Skip unknown spans to avoid corrupting offsets.
                continue

            year_val = item.get("year", candidate.year)
            if isinstance(year_val, str):
                cleaned_year = year_val.strip()
                if cleaned_year.isdigit():
                    year_val = int(cleaned_year)
                else:
                    year_val = candidate.year

            merged.append(
                MusicEntity(
                    name=item.get("name") or candidate.name,
                    artist=item.get("artist") or candidate.artist,
                    type=item.get("type") or candidate.type,
                    year=year_val,
                    latex_text=item.get("latex_text", candidate.latex_text),
                    start_index=_coerce_int(item.get("start_index"), candidate.start_index),
                    end_index=_coerce_int(item.get("end_index"), candidate.end_index),
                )
            )

        return merged

    def enrich(self, latex: str, candidates: list[MusicEntity]) -> list[MusicEntity]:
        system_prompt = self._system_prompt()
        payload = json.dumps(
            {
                "latex": latex,
                "candidates": self._serialize_candidates(candidates),
                "instruction_version": self.prompt_path.name,
            }
        )

        output = self._run_claude(system_prompt, payload)

        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise AgentError("Agent response was not valid JSON") from exc

        if isinstance(data, dict) and "entities" in data:
            raw_entities = data["entities"]
        elif isinstance(data, list):
            raw_entities = data
        else:
            raise AgentError("Agent response missing entities list")

        merged = self._merge_entities(raw_entities, candidates)
        if not merged:
            raise AgentError("Agent returned no usable entities")

        return merged


def _discover_entrypoint_agents() -> dict[str, Callable[..., AgentStrategy]]:
    factories: dict[str, Callable[..., AgentStrategy]] = {}
    try:
        for ep in entry_points().select(group="latex_music_linker.agents"):
            try:
                factories.setdefault(ep.name, ep.load())
            except Exception as exc:  # pragma: no cover - defensive logging
                LOG.debug("Failed to load agent entrypoint %s: %s", ep.name, exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        LOG.debug("Failed to read agent entry points: %s", exc)
    return factories


def agent_factories() -> dict[str, Callable[..., AgentStrategy]]:
    factories: dict[str, Callable[..., AgentStrategy]] = {
        "heuristic": HeuristicStrategy,
        "llm": LLMStrategy,
        "claude-code": ClaudeCodeStrategy,
    }
    factories.update(_discover_entrypoint_agents())
    return factories


def load_agent_strategy(name: str, **kwargs: Any) -> AgentStrategy:
    factories = agent_factories()
    factory = factories.get(name)
    if factory is None:
        raise AgentError(f"Unknown agent strategy: {name}")
    try:
        return factory(**kwargs)
    except Exception as exc:  # pragma: no cover - defensive wrapping
        raise AgentError(f"Failed to construct agent '{name}': {exc}") from exc


def apply_agent_strategy(
    latex: str,
    candidates: list[MusicEntity],
    agent_name: str,
    agent_options: dict[str, Any] | None = None,
) -> tuple[list[MusicEntity], str | None]:
    """Apply the requested agent and return entities plus an optional fallback reason."""

    if agent_name == "heuristic":
        return candidates, None

    agent_options = agent_options or {}
    try:
        strategy = load_agent_strategy(agent_name, **agent_options)
    except AgentError as exc:
        return candidates, str(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return candidates, str(exc)

    try:
        enriched = strategy.enrich(latex, candidates)
    except AgentError as exc:
        return candidates, str(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return candidates, str(exc)

    if not enriched:
        return candidates, "Agent returned no entities"

    return enriched, None
