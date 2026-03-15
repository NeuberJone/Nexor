from __future__ import annotations

from dataclasses import dataclass

ABORTED_CANDIDATE = "ABORTED_CANDIDATE"
PARTIAL_CANDIDATE = "PARTIAL_CANDIDATE"


@dataclass(frozen=True)
class SuspicionThresholds:
    """
    Regras centrais para classificar jobs suspeitos.

    min_planned_length_m
        Ignora jobs pequenos demais para evitar falso positivo.

    aborted_max_ratio
        Se o impresso efetivo for 5% ou menos do planejado, considera abortado.

    aborted_max_effective_m
        Mantém um piso absoluto de segurança para casos próximos de zero.

    partial_max_ratio
        Abaixo desse ratio o job entra como sinalização de parcial/revisão.

    partial_min_missing_m
        Diferença mínima absoluta para evitar ruído.

    Observação:
        PARTIAL_CANDIDATE não implica falha automática.
        É apenas sinalização para revisão do operador.
    """

    min_planned_length_m: float = 0.30
    aborted_max_ratio: float = 0.05
    aborted_max_effective_m: float = 0.05
    partial_max_ratio: float = 0.98
    partial_min_missing_m: float = 0.20


@dataclass(frozen=True)
class SuspicionDecision:
    is_suspect: bool
    category: str | None
    ratio: float | None
    missing_length_m: float
    reason: str | None


DEFAULT_THRESHOLDS = SuspicionThresholds()


def classify_suspicion(
    planned_length_m: float | None,
    effective_printed_length_m: float | None,
    thresholds: SuspicionThresholds = DEFAULT_THRESHOLDS,
) -> SuspicionDecision:
    planned = max(float(planned_length_m or 0.0), 0.0)
    effective = max(float(effective_printed_length_m or 0.0), 0.0)

    if planned <= 0:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=None,
            missing_length_m=0.0,
            reason="NO_PLANNED_LENGTH",
        )

    missing_length_m = max(planned - effective, 0.0)
    ratio = effective / planned if planned > 0 else None

    if planned < thresholds.min_planned_length_m:
        return SuspicionDecision(
            is_suspect=False,
            category=None,
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="BELOW_MIN_PLANNED_LENGTH",
        )

    # Abortado: imprimiu 5% ou menos da arte
    if effective <= thresholds.aborted_max_effective_m or (
        ratio is not None and ratio <= thresholds.aborted_max_ratio
    ):
        return SuspicionDecision(
            is_suspect=True,
            category=ABORTED_CANDIDATE,
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="VERY_LOW_EFFECTIVE_PRINTED",
        )

    # Parcial / revisão: imprimiu menos que a arte com tolerância
    if (
        ratio is not None
        and ratio < thresholds.partial_max_ratio
        and missing_length_m >= thresholds.partial_min_missing_m
    ):
        return SuspicionDecision(
            is_suspect=True,
            category=PARTIAL_CANDIDATE,
            ratio=ratio,
            missing_length_m=missing_length_m,
            reason="PRINTED_BELOW_EXPECTED",
        )

    return SuspicionDecision(
        is_suspect=False,
        category=None,
        ratio=ratio,
        missing_length_m=missing_length_m,
        reason=None,
    )


def should_auto_apply(decision: SuspicionDecision) -> bool:
    return decision.category == ABORTED_CANDIDATE
