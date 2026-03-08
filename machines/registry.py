"""
Machine registry for Nexor.

Responsible for resolving a production machine based on
the ComputerName present in printer logs.
"""


# Mapping ComputerName -> Machine ID used by Nexor
MACHINE_REGISTRY = {
    # EXEMPLOS — ajuste conforme suas máquinas reais
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

    if computer_name in MACHINE_REGISTRY:
        return MACHINE_REGISTRY[computer_name]

    if driver:
        return driver

    return "UNKNOWN_MACHINE"