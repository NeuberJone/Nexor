from storage.repository import ProductionRepository

repo = ProductionRepository()

updated_1 = repo.mark_as_failed(
    job_id="36000",
    computer_name="DESKTOP-36UB5C9",
    start_time_iso="2026-03-05T19:53:03",
    reason="Job parcial/interrompido",
    notes="Marcado manualmente após análise do log no modelo consumed/actual",
)

updated_2 = repo.mark_as_failed(
    job_id="36005",
    computer_name="DESKTOP-36UB5C9",
    start_time_iso="2026-03-05T19:55:40",
    reason="Job iniciado e interrompido no começo",
    notes="Marcado manualmente após análise do log no modelo consumed/actual",
)

print("36000 atualizado:", updated_1)
print("36005 atualizado:", updated_2)