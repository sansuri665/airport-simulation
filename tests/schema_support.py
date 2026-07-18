"""Compatibility imports for the production JSON Schema subset validator.

Keeping tests on the same implementation used by ``validate-config`` prevents
the command-line guard and contract tests from accepting different documents.
"""

from airport_sim.schema_validation import (
    SchemaValidationError,
    load_schema_registry,
    validate_named_schema,
    validate_schema,
)

__all__ = [
    "SchemaValidationError",
    "load_schema_registry",
    "validate_named_schema",
    "validate_schema",
]
