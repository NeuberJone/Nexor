from dataclasses import dataclass


ABORTED_CANDIDATE = "ABORTED_CANDIDATE"
PARTIAL_CANDIDATE = "PARTIAL_CANDIDATE"


@dataclass(frozen=True)
class SuspicionThresholds:
    min_planned_length_m: float = 0.30
    aborted_max_ratio: float = 0.15
    aborted_max_actual_m: float = 0.05
    partial_max_ratio: float = 0.90
    partial_min_missing_m: float = 0.20


@dataclass(frozen=True)
class SuspicionDecision:
    is_suspect: bool
    category: str | None
    ratio: float | None
    missing_length_m: float
    reason: str | None


DEFAULT_THRESHOLDS = SuspicionThresholds()


def classify_print_suspicion(
    planned_length_m: float | None,
    actual_printed_length_m: float | None,
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> SuspicionDecision:
    planned = max(planned_length_m or 0.0, 0.0)
    actual = max(actual_printed_length_m or 0.0, 0.0)

    if planned <= 0:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=None,
            missing_length_m=0.0,
            reason="NO_PLANNED_LENGTH",
        )

    missing = max(planned - actual, 0.0)
    ratio = actual / planned

    # ignora jobs pequenos demais para evitar falso positivo em teste/amostra
    if planned < thresholds.min_planned_length_m:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=ratio,
            missing_length_m=missing,
            reason="BELOW_MIN_PLANNED_LENGTH",
        )

    # abortado: saiu praticamente nada
    if actual <= thresholds.aborted_max_actual_m or ratio <= thresholds.aborted_max_ratio:
        return SuspicionDecision(
            is_suspect=True,
            category=ABORTED_CANDIDATE,
            ratio=ratio,
            missing_length_m=missing,
            reason="VERY_LOW_ACTUAL_PRINTED",
        )

    # parcial: saiu parte relevante, mas ficou bem abaixo do esperado
    if ratio < thresholds.partial_max_ratio and missing >= thresholds.partial_min_missing_m:
        return SuspicionDecision(
            is_suspect=True,
            category=PARTIAL_CANDIDATE,
            ratio=ratio,
            missing_length_m=missing,
            reason="PRINTED_BELOW_EXPECTED",
        )

    return SuspicionDecision(
        is_suspect=False,
        category=None,
        ratio=ratio,
        missing_length_m=missing,
        reason=None,
    )