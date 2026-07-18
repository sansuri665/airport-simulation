from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import storage
ensure_inside = storage.ensure_inside
read_json = storage.read_json
write_json = storage.write_json


def run_id_for(seed: int, years: int) -> str:
    return f"seed_{seed}_years_{years}"


def parse_run_id(run_id: str) -> tuple[int | None, int | None]:
    parts = run_id.split("_")
    try:
        seed_index = parts.index("seed") + 1
        years_index = parts.index("years") + 1
        return int(parts[seed_index]), int(parts[years_index])
    except (ValueError, IndexError):
        return None, None


@dataclass(frozen=True)
class SaveRepository:
    workspace_root: Path
    save_root: Path

    def save_path(self, seed: int, years: int) -> Path:
        save_dir = self.save_root / run_id_for(seed, years)
        return ensure_inside(self.save_root, save_dir / "dynamic_test_save.json")

    def summary(
        self,
        seed: int,
        years: int,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self.save_path(seed, years)
        if not payload:
            return {
                "label": "当前 seed 存档",
                "occupied": False,
                "seed": seed,
                "years": years,
                "runId": run_id_for(seed, years),
                "savePath": str(path.relative_to(self.workspace_root).as_posix()),
            }
        actions = payload.get("playerActions", [])
        return {
            "label": "当前 seed 存档",
            "occupied": True,
            "seed": payload.get("seed", seed),
            "years": payload.get("years", years),
            "mode": payload.get("mode"),
            "runId": payload.get("runId", run_id_for(seed, years)),
            "savePath": str(path.relative_to(self.workspace_root).as_posix()),
            "currentQuarterIndex": payload.get("currentQuarterIndex"),
            "currentLabel": payload.get("currentLabel", ""),
            "savedAt": payload.get("savedAt", ""),
            "savedAtUnix": payload.get("savedAtUnix", 0),
            "contractSignatureCount": len(payload.get("contractSignatures", {}) or {}),
            "playerActionCount": len(actions or []),
            "projectActionCount": len(
                [action for action in actions if action.get("type") == "start_project"]
            ),
            "slotRenameCount": len(
                [action for action in actions if action.get("type") == "rename_slot"]
            ),
            "operationOverrideQuarterCount": 0,
        }

    def read(self, seed: int, years: int) -> dict[str, Any] | None:
        path = self.save_path(seed, years)
        if not path.exists():
            return None
        payload = read_json(path)
        payload["seed"] = seed
        payload["years"] = years
        payload["runId"] = run_id_for(seed, years)
        return payload

    def clear(self, seed: int, years: int) -> None:
        path = self.save_path(seed, years)
        if path.exists():
            path.unlink()
