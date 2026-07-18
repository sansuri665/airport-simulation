from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class RunLifecycleDependencies:
    time_module: Any
    process_id: Callable[[], int]
    resolve_path: Callable[[Path], Path]
    resolve_seed: Callable[[argparse.Namespace], int]
    clean_run_id: Callable[[str], str]
    write_run_index: Callable[[Path], dict[str, Any]]
    build_run_in_directory: Callable[
        [argparse.Namespace, int, str, Path, Path],
        dict[str, Any],
    ]
    requested_publish_variant: Callable[[argparse.Namespace, dict[str, Any]], str | None]
    write_validated_run_manifest: Callable[[Path, dict[str, Any]], None]
    replace_directory_with_retry: Callable[[Path, Path], None]
    remove_tree: Callable[[Path], None]
    publish_variant_to_viewer: Callable[[Path, Path], dict[str, Any]]
    write_json_file: Callable[[Path, Any], None]


def execute_run(
    args: argparse.Namespace,
    *,
    dependencies: RunLifecycleDependencies,
) -> dict[str, Any]:
    output_root = dependencies.resolve_path(Path(args.output_root))
    if getattr(args, "artifact_profile", "full") != "full" and args.publish_viewer != "none":
        raise ValueError("--artifact-profile seed-cache cannot be combined with --publish-viewer")
    if args.index_only:
        return dependencies.write_run_index(output_root)

    seed = dependencies.resolve_seed(args)
    timestamp = dependencies.time_module.strftime("%Y%m%d_%H%M%S")
    run_id = dependencies.clean_run_id(args.run_id or f"run_{timestamp}_seed_{seed}")
    final_run_dir = output_root / run_id
    staging_dir = (
        output_root
        / f".staging_{dependencies.process_id()}_{dependencies.time_module.time_ns():x}"
    )
    output_root.mkdir(parents=True, exist_ok=True)
    if final_run_dir.exists():
        raise FileExistsError(f"Run already exists and will not be overwritten: {final_run_dir}")

    try:
        staging_dir.mkdir()
        manifest = dependencies.build_run_in_directory(
            args,
            seed,
            run_id,
            staging_dir,
            final_run_dir,
        )
        publish_name = dependencies.requested_publish_variant(args, manifest)
        dependencies.write_validated_run_manifest(staging_dir, manifest)
        dependencies.replace_directory_with_retry(staging_dir, final_run_dir)
    except Exception:
        if (
            staging_dir.exists()
            and dependencies.resolve_path(staging_dir.parent) == output_root
        ):
            dependencies.remove_tree(staging_dir)
        raise

    if publish_name is not None:
        manifest["published"] = {
            "variant": publish_name,
            **dependencies.publish_variant_to_viewer(
                final_run_dir / publish_name,
                Path(args.viewer_output_root),
            ),
        }
        dependencies.write_json_file(final_run_dir / "manifest.json", manifest)

    manifest["run_index"] = dependencies.write_run_index(output_root)
    dependencies.write_json_file(final_run_dir / "manifest.json", manifest)
    return manifest
