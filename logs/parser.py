import re
from core.exceptions import LogParseError

SECTION_RE = re.compile(r"\[(.+?)\]")
KEY_VALUE_RE = re.compile(r"([^=]+)=(.+)")


def parse_log_text(text: str) -> dict:

    if not text.strip():
        raise LogParseError("Empty log")

    sections = {}
    current_section = None

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        section_match = SECTION_RE.match(line)

        if section_match:
            current_section = section_match.group(1)
            sections[current_section] = {}
            continue

        kv_match = KEY_VALUE_RE.match(line)

        if kv_match and current_section:

            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()

            sections[current_section][key] = value

    return sections