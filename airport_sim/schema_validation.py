from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    """A JSON Schema subset violation with a stable instance location."""

    def __init__(self, location: str, message: str) -> None:
        self.location = location
        self.message = message
        super().__init__(f"{location}: {message}")


def load_schema_registry(schema_root: Path) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_root.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(schema, dict):
            raise SchemaValidationError("$", f"schema document is not an object: {path}")
        for key in (path.name, schema.get("$id")):
            if not isinstance(key, str) or not key:
                continue
            if key in registry:
                raise SchemaValidationError("$", f"duplicate schema registry key: {key}")
            registry[key] = schema
    return registry


def _resolve_pointer(document: Any, pointer: str) -> Any:
    if not pointer:
        return document
    if not pointer.startswith("/"):
        raise SchemaValidationError("$", f"unsupported JSON pointer: #{pointer}")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise SchemaValidationError("$", f"unresolved JSON pointer: #{pointer}")
        current = current[part]
    return current


def _resolve_ref(
    reference: str,
    current_name: str,
    registry: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    target_name, separator, fragment = reference.partition("#")
    target_name = target_name or current_name
    if target_name not in registry:
        target_name = target_name.rsplit("/", 1)[-1]
    if target_name not in registry:
        raise SchemaValidationError("$", f"unknown schema reference: {reference}")
    target_document = registry[target_name]
    target = _resolve_pointer(target_document, fragment if separator else "")
    if not isinstance(target, dict):
        raise SchemaValidationError("$", f"schema reference is not an object: {reference}")
    return target, target_name


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise SchemaValidationError("$", f"unsupported schema type: {expected}")


def _child_location(location: str, key: str) -> str:
    return f"{location}.{key}" if key.isidentifier() else f"{location}[{key!r}]"


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    *,
    current_name: str,
    location: str = "$",
) -> None:
    if "$ref" in schema:
        target, target_name = _resolve_ref(str(schema["$ref"]), current_name, registry)
        validate_schema(
            value,
            target,
            registry,
            current_name=target_name,
            location=location,
        )

    for part in schema.get("allOf", []):
        validate_schema(
            value,
            part,
            registry,
            current_name=current_name,
            location=location,
        )

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(
            location,
            f"expected const {schema['const']!r}, got {value!r}",
        )
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(location, f"{value!r} is not in {schema['enum']!r}")

    expected_types = schema.get("type")
    if expected_types is not None:
        expected = [expected_types] if isinstance(expected_types, str) else list(expected_types)
        if not any(_matches_type(value, item) for item in expected):
            raise SchemaValidationError(
                location,
                f"expected type {expected!r}, got {type(value).__name__}",
            )

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise SchemaValidationError(location, f"missing required keys {missing!r}")
        minimum_properties = schema.get("minProperties")
        if minimum_properties is not None and len(value) < int(minimum_properties):
            raise SchemaValidationError(
                location,
                f"expected at least {minimum_properties} properties",
            )
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                validate_schema(
                    value[key],
                    child_schema,
                    registry,
                    current_name=current_name,
                    location=_child_location(location, str(key)),
                )
        additional = schema.get("additionalProperties", True)
        unknown = [key for key in value if key not in properties]
        if additional is False and unknown:
            raise SchemaValidationError(location, f"unexpected keys {unknown!r}")
        if isinstance(additional, dict):
            for key in unknown:
                validate_schema(
                    value[key],
                    additional,
                    registry,
                    current_name=current_name,
                    location=_child_location(location, str(key)),
                )

    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if minimum_items is not None and len(value) < int(minimum_items):
            raise SchemaValidationError(location, f"expected at least {minimum_items} items")
        maximum_items = schema.get("maxItems")
        if maximum_items is not None and len(value) > int(maximum_items):
            raise SchemaValidationError(location, f"expected at most {maximum_items} items")
        if schema.get("uniqueItems"):
            for index, item in enumerate(value):
                if any(item == earlier for earlier in value[:index]):
                    raise SchemaValidationError(
                        f"{location}[{index}]",
                        "array items must be unique",
                    )
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate_schema(
                    item,
                    item_schema,
                    registry,
                    current_name=current_name,
                    location=f"{location}[{index}]",
                )

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None and len(value) < int(minimum_length):
            raise SchemaValidationError(
                location,
                f"string is shorter than minimum length {minimum_length}",
            )
        pattern = schema.get("pattern")
        if pattern is not None and re.search(str(pattern), value) is None:
            raise SchemaValidationError(location, f"{value!r} does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(float(value)):
            raise SchemaValidationError(location, "number must be finite")
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise SchemaValidationError(
                location,
                f"{value!r} is less than minimum {minimum!r}",
            )
        maximum = schema.get("maximum")
        if maximum is not None and value > maximum:
            raise SchemaValidationError(
                location,
                f"{value!r} is greater than maximum {maximum!r}",
            )


def validate_named_schema(
    value: Any,
    schema_name: str,
    registry: dict[str, dict[str, Any]],
) -> None:
    if schema_name not in registry:
        raise SchemaValidationError("$", f"schema is not registered: {schema_name}")
    validate_schema(
        value,
        registry[schema_name],
        registry,
        current_name=schema_name,
    )
