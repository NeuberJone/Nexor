from __future__ import annotations

from core.exceptions import LogValidationError
from core.models import Machine
from logs.mapper import map_sections_to_job
from logs.parser import parse_log_text


def test_parse_and_map_basic_log():
    raw_log = """
[General]
ComputerName = DESKTOP-2GGH09O
SoftwareVersion = 10.0.17
JobID = 10864
Document = Pedido 1001 - Dryfit - file.jpeg
StartTime = 03/03/2026 23:19:28
EndTime = 03/03/2026 23:22:07
Driver = Mimaki TS55-1800

[1]
HeightMM = 1101.0
VPosMM = 1054.5
""".strip()

    sections = parse_log_text(raw_log)
    registry = {
        "DESKTOP-2GGH09O": Machine(
            machine_id="M2",
            name="M2",
            computer_name="DESKTOP-2GGH09O",
            model="Mimaki TS55-1800",
        )
    }

    job = map_sections_to_job(sections, machine_registry=registry)

    assert job.job_id == "10864"
    assert job.machine == "M2"
    assert job.computer_name == "DESKTOP-2GGH09O"
    assert job.document == "Pedido 1001 - Dryfit - file.jpeg"
    assert job.duration_seconds == 159
    assert job.fabric == "DRYFIT"

    # Regra crítica:
    assert job.length_m == 1.101
    assert job.gap_before_m == 1.0545

    # Não pode somar VPosMM ao comprimento do arquivo
    assert job.length_m != 2.1555


def test_accepts_vpositionmm_legacy_name():
    raw_log = """
[General]
ComputerName = DESKTOP-2GGH09O
JobID = 10865
Document = file.jpeg
StartTime = 03/03/2026 10:00:00
EndTime = 03/03/2026 10:01:30
Driver = Mimaki TS55-1800

[1]
HeightMM = 500
VPositionMM = 250
""".strip()

    sections = parse_log_text(raw_log)
    job = map_sections_to_job(sections)

    assert job.length_m == 0.5
    assert job.gap_before_m == 0.25
    assert job.duration_seconds == 90


def test_falls_back_to_driver_when_machine_not_registered():
    raw_log = """
[General]
ComputerName = PC-UNKNOWN
JobID = 10866
Document = file.jpeg
StartTime = 03/03/2026 12:00:00
EndTime = 03/03/2026 12:02:00
Driver = Mimaki TS55-1800

[1]
HeightMM = 800
VPosMM = 100
""".strip()

    sections = parse_log_text(raw_log)
    job = map_sections_to_job(sections)

    assert job.machine == "Mimaki TS55-1800"
    assert job.computer_name == "PC-UNKNOWN"


def test_raises_when_job_id_is_missing():
    raw_log = """
[General]
ComputerName = DESKTOP-2GGH09O
Document = file.jpeg
StartTime = 03/03/2026 23:19:28
EndTime = 03/03/2026 23:22:07
Driver = Mimaki TS55-1800
""".strip()

    sections = parse_log_text(raw_log)

    try:
        map_sections_to_job(sections)
        assert False, "Era esperado LogValidationError"
    except LogValidationError as exc:
        assert "JobID" in str(exc)


def test_raises_when_end_time_is_before_start_time():
    raw_log = """
[General]
ComputerName = DESKTOP-2GGH09O
JobID = 10867
Document = file.jpeg
StartTime = 03/03/2026 23:22:07
EndTime = 03/03/2026 23:19:28
Driver = Mimaki TS55-1800

[1]
HeightMM = 1000
VPosMM = 0
""".strip()

    sections = parse_log_text(raw_log)

    try:
        map_sections_to_job(sections)
        assert False, "Era esperado LogValidationError"
    except LogValidationError as exc:
        assert "EndTime anterior" in str(exc)