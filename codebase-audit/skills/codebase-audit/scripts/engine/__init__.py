"""Deterministic scoring/gate/report engine for codebase-audit."""

__version__ = "1.1.0"

# audit key -> ISO/IEC 25010 characteristic (used for error placeholders)
DIMENSIONS = {
    "performance": "Performance Efficiency",
    "security": "Security",
    "enterprise": "Reliability",
    "issues": "Maintainability",
    "architecture": "Reliability",
    "dependencies": "Security",
    "i18n": "Portability",
    "api": "Compatibility",
    "resilience": "Fault Tolerance",
    "container_iac": "Portability",
    "observability": "Operability",
}
