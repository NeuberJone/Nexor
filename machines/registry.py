"""
Machine registry for Nexor.

Responsible for resolving a production machine based on
the ComputerName present in printer logs.
"""


# Mapping ComputerName -> Machine ID used by Nexor
MACHINE_REGISTRY = {
    # Ajuste conforme suas máquinas reais
    "DESKTOP-36UB5C9": "M1",
    "DESKTOP-2GGH09O": "M2",
}


def resolve_machine(computer_name: str, driver: str | None = None) -> str:
    """
    Resolve the machine identifier used internally by Nexor.

    Priority:
    1) Known ComputerName in registry
    2) Driver name (fallback)
    3) UNKNOWN_MACHINE
    """
    normalized = (computer_name or "").strip()

    if normalized in MACHINE_REGISTRY:
        return MACHINE_REGISTRY[normalized]

    if driver:
        return driver

    return "UNKNOWN_MACHINE"


def register_machine(computer_name: str, machine_id: str) -> None:
    """
    Add or update a machine mapping.
    """
    normalized_computer = (computer_name or "").strip()
    normalized_machine = (machine_id or "").strip().upper()

    if not normalized_computer:
        raise ValueError("computer_name cannot be empty")

    if not normalized_machine:
        raise ValueError("machine_id cannot be empty")

    MACHINE_REGISTRY[normalized_computer] = normalized_machine


def remove_machine(computer_name: str) -> bool:
    """
    Remove a machine mapping by ComputerName.
    Returns True if removed, False if not found.
    """
    normalized = (computer_name or "").strip()

    if normalized in MACHINE_REGISTRY:
        del MACHINE_REGISTRY[normalized]
        return True

    return False


def list_registered_machines() -> dict[str, str]:
    """
    Return a copy of the current machine registry.
    """
    return dict(MACHINE_REGISTRY)