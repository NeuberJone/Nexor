from __future__ import annotations

import re
from pathlib import Path

from core.exceptions import LogParseError

_RE_SECTION = re.compile(r"^\s*\[(.+?)\]\s*$")
_RE_KV = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")


def parse_log_text(text: str) -> dict[str, dict[str, str]]:
    """
    Converte o conteúdo bruto do log em seções -> chave/valor.
    Exemplo de retorno:
    {
        "General": {"JobID": "10864", ...},
        "1": {"HeightMM": "1101.0", ...},
    }
    """
    if not text or not text.strip():
        raise LogParseError("Log vazio.")

    sections: dict[str, dict[str, str]] = {}
    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        section_match = _RE_SECTION.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            sections.setdefault(current_section, {})
            continue

        kv_match = _RE_KV.match(line)
        if kv_match and current_section:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()
            sections[current_section][key] = value

    if not sections:
        raise LogParseError("Nenhuma seção válida encontrada no log.")

    return sections


def parse_log_file(path: str | Path) -> dict[str, dict[str, str]]:
    file_path = Path(path)

    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise LogParseError(f"Não foi possível ler o arquivo: {file_path}") from exc

    return parse_log_text(text)