from pathlib import Path
from logs.parser import parse_log_text
from logs.mapper import map_sections_to_job


def import_job_from_log(path):

    path = Path(path)

    text = path.read_text(encoding="utf-8", errors="ignore")

    sections = parse_log_text(text)

    job = map_sections_to_job(sections)

    job.source_path = str(path)

    return job